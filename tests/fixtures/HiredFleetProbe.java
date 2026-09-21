package citysim;

import java.util.*;
import org.matsim.api.core.v01.*;
import org.matsim.api.core.v01.events.*;
import org.matsim.api.core.v01.network.*;
import org.matsim.api.core.v01.population.*;
import org.matsim.core.config.*;
import org.matsim.core.config.groups.QSimConfigGroup;
import org.matsim.core.events.EventsUtils;
import org.matsim.core.events.handler.BasicEventHandler;
import org.matsim.core.mobsim.qsim.*;
import org.matsim.core.mobsim.qsim.qnetsimengine.QNetsimEngineModule;
import org.matsim.core.population.routes.RouteUtils;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.scoring.EventsToLegs;
import org.matsim.vehicles.*;

/** Synthetic supply experiment: no city observation or model coefficient. */
public final class HiredFleetProbe {
    static void require(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
    static List<Event> run(int units, double maxWait, double endTime) {
        HiredFleetConfigGroup fleet = new HiredFleetConfigGroup();
        fleet.representation = "pooled_queue";
        fleet.vehiclesByMode = "compact:" + units + ",cab:1";
        fleet.maxWaitSeconds = maxWait; fleet.turnaroundSeconds = 20;
        Config config = ConfigUtils.createConfig(fleet);
        config.routing().setNetworkModes(Set.of("compact", "cab"));
        config.qsim().setMainModes(Set.of("compact", "cab"));
        config.qsim().setVehiclesSource(QSimConfigGroup.VehiclesSource.modeVehicleTypesFromVehiclesData);
        config.qsim().setNumberOfThreads(1); config.qsim().setEndTime(endTime);
        config.qsim().setStuckTime(1000);
        config.qsim().setVehicleBehavior(QSimConfigGroup.VehicleBehavior.teleport);
        fleet.checkConsistency(config);
        Scenario s = ScenarioUtils.createScenario(config); Network n = s.getNetwork();
        for (int i=0; i<4; i++) n.addNode(n.getFactory().createNode(Id.createNodeId(i), new Coord(i*1000,0)));
        for (int i=0; i<3; i++) {
            Link l=n.getFactory().createLink(Id.createLinkId(i),n.getNodes().get(Id.createNodeId(i)),n.getNodes().get(Id.createNodeId(i+1)));
            l.setLength(1000); l.setFreespeed(10); l.setCapacity(10000); l.setNumberOfLanes(2);
            l.setAllowedModes(Set.of("compact","cab")); n.addLink(l);
        }
        var f=s.getPopulation().getFactory();
        for (String mode: List.of("compact","cab")) {
            VehicleType type=VehicleUtils.createVehicleType(Id.create(mode,VehicleType.class));
            type.setNetworkMode(mode); type.setMaximumVelocity(10); s.getVehicles().addVehicleType(type);
        }
        for(int i=0;i<4;i++) {
            String mode=i==3?"cab":"compact"; Person p=f.createPerson(Id.createPersonId("p"+i));
            var vehicle=VehicleUtils.createVehicle(Id.createVehicleId(p.getId()),s.getVehicles().getVehicleTypes().get(Id.create(mode,VehicleType.class)));
            s.getVehicles().addVehicle(vehicle); VehicleUtils.insertVehicleIdsIntoAttributes(p,Map.of(mode,vehicle.getId()));
            Plan plan=f.createPlan(); Activity a=f.createActivityFromLinkId("home",Id.createLinkId(0)); a.setEndTime(100);
            Leg leg=f.createLeg(mode); var route=RouteUtils.createLinkNetworkRouteImpl(Id.createLinkId(0),Id.createLinkId(2));
            route.setLinkIds(Id.createLinkId(0),List.of(Id.createLinkId(1)),Id.createLinkId(2));
            route.setVehicleId(vehicle.getId()); route.setTravelTime(100); leg.setRoute(route);
            plan.addActivity(a); plan.addLeg(leg); plan.addActivity(f.createActivityFromLinkId("work",Id.createLinkId(2)));
            p.addPlan(plan); s.getPopulation().addPerson(p);
        }
        List<Event> observed=new ArrayList<>(); var events=EventsUtils.createEventsManager();
        events.addHandler((BasicEventHandler)observed::add);
        Map<Id<Person>, Leg> experienced = new HashMap<>();
        EventsToLegs scoringLegs = new EventsToLegs(s);
        scoringLegs.addLegHandler(l -> experienced.put(l.getAgentId(), l.getLeg()));
        events.addHandler(scoringLegs);
        QSimBuilder builder=new QSimBuilder(config).useDefaults();
        builder.addOverridingQSimModule(new AbstractQSimModule() {
            @Override protected void configureQSim() {
                bind(HiredFleetQueue.class).asEagerSingleton();
                addQSimComponentBinding(HiredFleetQueue.COMPONENT).to(HiredFleetQueue.class);
            }
        });
        builder.configureQSimComponents(c -> {
            c.removeNamedComponent(QNetsimEngineModule.COMPONENT_NAME);
            c.removeNamedComponent(TeleportationModule.COMPONENT_NAME);
            c.addNamedComponent(HiredFleetQueue.COMPONENT);
            c.addNamedComponent(QNetsimEngineModule.COMPONENT_NAME);
            c.addNamedComponent(TeleportationModule.COMPONENT_NAME);
        });
        QSim sim=builder.build(s,events); events.initProcessing(); sim.run(); events.finishProcessing();
        for (Event event : observed) {
            if (event instanceof PersonArrivalEvent arrival) {
                Leg leg = experienced.get(arrival.getPersonId());
                require(leg != null && leg.getTravelTime().seconds() == arrival.getTime() - 100,
                        "native scoring leg excluded supply waiting");
            }
        }
        return observed;
    }
    static Map<String,Double> times(List<Event> events, boolean arrivals) {
        Map<String,Double> out=new TreeMap<>();
        for(Event e:events) {
            if(arrivals && e instanceof PersonArrivalEvent a) out.put(a.getPersonId().toString(),a.getTime());
            if(!arrivals && e instanceof VehicleEntersTrafficEvent a) out.put(a.getPersonId().toString(),a.getTime());
        }
        return out;
    }
    public static void main(String[] args) {
        List<Event> observed=run(1,1000,2000);
        var arrivals=times(observed,true); var enters=times(observed,false);
        require(arrivals.size()==4,"queued passengers did not all arrive");
        require(enters.get("p1")>=arrivals.get("p0")+20,"unit reused before actual arrival and turnaround");
        require(enters.get("p2")>=arrivals.get("p1")+20,"second queued trip escaped fleet");
        require(enters.get("p3")<arrivals.get("p0"),"independent cab pool was blocked");
        require(observed.stream().filter(e->e instanceof LinkEnterEvent).count()>=4,"passengers did not traverse roads");
        require(observed.stream().noneMatch(e->e instanceof PersonStuckEvent),"unexpected stuck traveller");
        List<Event> ample=run(3,1000,2000);
        require(times(ample,true).get("p2")<arrivals.get("p2"),"supply did not affect experienced arrival time");
        List<Event> none=run(0,10,2000);
        require(times(none,true).keySet().equals(Set.of("p3")),"zero fleet dispatched a vehicle");
        require(none.stream().filter(e->e instanceof PersonStuckEvent).count()==3,"timeout not recorded natively");
        List<Event> cutoff=run(0,1000,150);
        require(cutoff.stream().filter(e->e instanceof PersonStuckEvent).count()>=3,"pending agents lost at simulation end");
        System.out.println("PASS hired fleet: actual arrivals release supply, physical queued travel, native scoring includes waiting, independent modes, supply response, zero supply, timeout and end cleanup");
    }
}
