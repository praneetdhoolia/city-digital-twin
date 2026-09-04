package citysim;

import com.google.inject.Singleton;
import java.io.File;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.AbstractModule;
import org.matsim.core.controler.Controler;
import org.matsim.core.mobsim.qsim.AbstractQSimModule;
import org.matsim.core.mobsim.qsim.PopulationModule;
import org.matsim.core.mobsim.qsim.TeleportationModule;
import org.matsim.core.mobsim.qsim.qnetsimengine.QNetsimEngineModule;
import org.matsim.core.population.algorithms.PermissibleModesCalculator;
import org.matsim.core.scenario.ScenarioUtils;

/**
 * The project's MATSim entry point. Identical to
 * {@code org.matsim.core.controler.Controler} except for the two rebindings and
 * the one added module below.
 *
 * <p><b>1. Mode availability.</b> {@link PermissibleModesCalculator} is rebound
 * so `ride` can be withheld from a person who has nobody to drive them
 * (DECISIONS.md 9.11), `bike` from a person drawn without one (DECISIONS.md
 * 9.39, issue #29), and so an agent carrying `lockedMode` — a through-traffic
 * vehicle anchored on an observed road count — keeps the mode it is defined by
 * (DECISIONS.md 9.41, issue #20).
 *
 * <p><b>2. Ride travel time (DECISIONS.md 9.26, issue #28).</b> `ride` is listed
 * in {@code routing.networkModes} but is not the qsim {@code mainMode}, so
 * MATSim routes it over the network and — with no events of its own to learn
 * from — hands it <em>free-flow</em> link times. Measured over a completed
 * 250-iteration run that made a car passenger arrive 13% faster than the car
 * carrying them: ride realised 55.7 km/h against car's 49.3. The two bindings
 * below point `ride` at the congested car travel time and the car disutility, so
 * a passenger now experiences exactly the traffic the driver does.
 *
 * <p>Note what this deliberately does <em>not</em> do: it does not add a ride
 * vehicle to the mobsim. A passenger travels in a car that is already there, so
 * a second vehicle would double-count the traffic. Ride therefore
 * <em>experiences</em> congestion without <em>causing</em> it — which is correct
 * only insofar as every ride trip is paired with a driver trip, and it is not.
 * That is issue #31, and it is open.
 *
 * <p><b>3. Parking charges (DECISIONS.md 9.31, issue #33).</b> The package has
 * declared a parking price since P1 and no script read it, so a car has always
 * parked for free — in a study about city-centre access, where parking price is
 * the prime competitive lever between car and public transport. When the
 * `parking` module carries a price file, {@link ParkingChargeHandler} is
 * installed and bills a car for the time it stands still. The module is absent
 * from a config that does not want it, and the handler is then never built.
 *
 * <p><b>4. Ride pairing, Tier 1 (DECISIONS.md 9.44, issue #31).</b> The note
 * above says ride experiences congestion without causing it, "which is correct
 * only insofar as every ride trip is paired with a driver trip, and it is not".
 * {@link RidePairingEngine} is what makes that pairing exist: at the
 * BeforeMobsim boundary each `ride` leg looks up a household member whose `car`
 * leg it could be inside, and a paired passenger then takes THAT DRIVER's
 * realised travel time rather than its own routed one. The module is absent
 * from a config that does not want it, and `ridePairing.enabled = false`
 * restores exactly the previous behaviour for comparison within one build.
 *
 * <p><b>5. Live telemetry.</b> When the `telemetry` module is present,
 * {@link RunTelemetry} publishes what is moving, of what kind and where it is
 * piling up, <em>while the mobsim runs</em>. It needs no change to
 * {@code writeEventsInterval}: a registered handler receives the full event
 * stream on every iteration regardless of whether that stream is also being
 * written to disk. It is an observer and cannot alter a result.
 *
 * <p>Run exactly as the stock main was:
 * <pre>java -cp pt2matsim-shaded.jar;classes citysim.CitysimControler config.xml</pre>
 *
 * <p>The pinned toolchain is untouched: this ADDS a compiled artefact alongside
 * the shaded jar rather than replacing it, so the JDK, pt2matsim and SUMO
 * digests in .tools/toolchain.json are unchanged. The artefact is built from
 * committed source by the pinned javac, which is what makes it reproducible.
 */
public final class CitysimControler {

    private CitysimControler() {
    }

    public static void main(final String[] args) {
        if (args.length != 1) {
            System.err.println("usage: citysim.CitysimControler <config.xml>");
            System.exit(2);
        }
        quietenAccessEgressWarning();
        assemble(args[0], java.util.List.of()).run();
    }

    /**
     * Silence ONE logger: {@code NetworkRoutingProvider}'s
     * "Using deprecated routing module without access/egress" warning.
     *
     * <p>It fires seven lines every time a routing-module provider is asked
     * for a module, because {@code routing.accessEgressType = none} is what
     * this model runs on - deliberately, and it is load-bearing:
     * {@link ActivityLinkAssigner} exists precisely because access and egress
     * are not routed, so the setting is not the thing to change.
     *
     * <p>The F23 arm wrote 54.9 GB of {@code matsim.log} and the same again to
     * {@code output/logfile.log} and {@code output/logfileWarningsErrors.log} -
     * about 164 GiB, ~1.6 GiB an iteration, essentially all of it this one
     * warning, emitted through a caller-location-aware synchronous appender.
     * The CAUSE was the ride pairing building a whole TripRouter per detour
     * segment ({@link RidePairingEngine}, now one per iteration), and that is
     * fixed on its own terms; this line stops the remaining handful from being
     * a disk-space question at all, and stops any future unscoped provider
     * call from becoming one. Nothing else moves: the level is raised for this
     * one logger, so the same run emits the same events and the same plans.
     *
     * <p>The only log4j configuration otherwise in play is the {@code
     * log4j2.xml} inside the pinned MATSim jar; there is no project config and
     * the launcher passes no {@code -Dlog4j2.configurationFile}, so this is
     * where the decision has to be recorded.
     */
    static void quietenAccessEgressWarning() {
        org.apache.logging.log4j.core.config.Configurator.setLevel(
                "org.matsim.core.router.NetworkRoutingProvider",
                org.apache.logging.log4j.Level.ERROR);
    }

    /**
     * Build the citysim Controler exactly as {@code main} always has, and
     * RETURN it without running it.
     *
     * <p>Extracted (issue #73) so the signal-enabled entry point in
     * {@code src/java_signals/} can take the SAME assembly — every rebinding,
     * every QSim component reordering, byte for byte — and add the signals
     * contrib wiring on top before calling {@code run()}. The extraction is
     * behaviour-preserving: {@code main} is now
     * {@code assemble(args[0], List.of()).run()}, nothing else moved.
     *
     * <p>{@code extraGroups} are additional custom config groups registered
     * BEFORE the config file is parsed, exactly like the three citysim groups
     * below — an unrecognised parameter in one of their modules then fails the
     * run instead of being ignored. This class never imports the signals
     * contrib: src/java compiles against the shaded pt2matsim jar alone
     * (DECISIONS.md 9.73), so the extras arrive as plain
     * {@link org.matsim.core.config.ConfigGroup}s.
     */
    public static Controler assemble(
            final String configPath,
            final java.util.List<org.matsim.core.config.ConfigGroup> extraGroups) {
        final ParkingConfigGroup parking = new ParkingConfigGroup();
        final TelemetryConfigGroup telemetry = new TelemetryConfigGroup();
        final RidePairingConfigGroup ridePairing = new RidePairingConfigGroup();
        final FareConfigGroup fare = new FareConfigGroup();
        // Registered on EVERY stack even though only the signals entry point
        // reads it: the tramPriority module is emitted into every config (its
        // fields are registry-bound so the reach probe must see them move),
        // and this MATSim REFUSES an unmaterialised module at the consistency
        // check - "Unmaterialized config group: tramPriority", measured on
        // the first detached smoke probe. The group class has no signals
        // imports, so the base compile stays clean; the CONTROLLER that acts
        // on it exists only in src/java_signals/.
        final TramPriorityConfigGroup tramPriority = new TramPriorityConfigGroup();
        // SCATS adaptive control (DECISIONS.md 9.88, #73), registered on
        // every stack for exactly the reason above: its fields are
        // registry-bound, so the `scats` module is emitted into every
        // config and an unmaterialised group would fail the consistency
        // check. Only citysim.ScatsSignalController - which lives in
        // src/java_signals/ - ever acts on it.
        final ScatsConfigGroup scats = new ScatsConfigGroup();
        // Taxi as a finite fleet (9.99, #90), registered on every stack
        // for the same reason as the two above: its fields are
        // registry-bound, so the `taxiFleet` module is emitted into every
        // config and an unmaterialised group fails the consistency check.
        final TaxiFleetConfigGroup taxiFleet = new TaxiFleetConfigGroup();
        // The swissRailRaptor module (#49 Tier C, DECISIONS.md 9.78) needs its
        // typed group registered BEFORE the config is parsed, exactly like
        // tramPriority above: MATSim's UnmaterializedConfigGroupChecker throws
        // a RuntimeException for any module left as a generic ConfigGroup
        // (read from the pinned jar), and nothing materialises the raptor
        // group until the router is first built - after the check. Registered
        // on every stack, whether or not the emitted config carries the
        // module: with no module in the file this only installs the group's
        // own defaults (mode mapping off), and an unrecognised parameter in
        // an emitted module then fails the run instead of being ignored.
        final ch.sbb.matsim.config.SwissRailRaptorConfigGroup swissRailRaptor =
                new ch.sbb.matsim.config.SwissRailRaptorConfigGroup();
        // Gradient in walk/bike link travel time (DECISIONS.md 9.84, #21) and
        // the age availability gates (9.84, #49/#50). Registered on every
        // stack like tramPriority: the modules are emitted into every config
        // once their registry fields exist, and an unmaterialised module
        // fails MATSim's consistency check.
        final GradientConfigGroup gradient = new GradientConfigGroup();
        final ModeAvailabilityConfigGroup modeAvailability =
                new ModeAvailabilityConfigGroup();
        // The PT router's direct-walk basis (DECISIONS.md 9.121, #94):
        // registered on every stack like the others; absent from the
        // emitted config it defaults to the stock beeline behaviour.
        final PtDirectWalkConfigGroup ptDirectWalk = new PtDirectWalkConfigGroup();
        // The published Opal fare schedule (DECISIONS.md 9.135, #98):
        // registered on every stack like the others; absent from the emitted
        // config the group holds only sentinels, isEnabled() is false and
        // no handler is installed - every ride is then free, which is
        // exactly the pre-9.135 model.
        final PtFareConfigGroup ptFare = new PtFareConfigGroup();
        // Motor-traffic cycling stress (DECISIONS.md 9.138, #107) and
        // income-dependent money sensitivity (9.138, #108): registered on
        // every stack like the others; absent from the emitted config each
        // group holds representation=absent and nothing below installs.
        final BikeStressConfigGroup bikeStress = new BikeStressConfigGroup();
        final IncomeScoringConfigGroup incomeScoring =
                new IncomeScoringConfigGroup();
        final org.matsim.core.config.ConfigGroup[] groups =
                new org.matsim.core.config.ConfigGroup[14 + extraGroups.size()];
        groups[0] = parking;
        groups[1] = telemetry;
        groups[2] = ridePairing;
        groups[3] = fare;
        groups[4] = tramPriority;
        groups[5] = swissRailRaptor;
        groups[6] = gradient;
        groups[7] = modeAvailability;
        groups[8] = scats;
        groups[9] = taxiFleet;
        groups[10] = ptDirectWalk;
        groups[11] = ptFare;
        groups[12] = bikeStress;
        groups[13] = incomeScoring;
        for (int i = 0; i < extraGroups.size(); i++) {
            groups[14 + i] = extraGroups.get(i);
        }
        final Config config = ConfigUtils.loadConfig(configPath, groups);
        // The price file is written beside the config, like the network and the
        // schedule, so it is named relatively there and resolved here. MATSim
        // resolves its own input paths against the config's directory; this
        // module is ours, so it does its own.
        if (!parking.getPriceFile().isEmpty()) {
            final File declared = new File(parking.getPriceFile());
            if (!declared.isAbsolute()) {
                final File base =
                        new File(configPath).getAbsoluteFile().getParentFile();
                parking.setPriceFile(new File(base, parking.getPriceFile()).getPath());
            }
        }
        final org.matsim.api.core.v01.Scenario scenario =
                ScenarioUtils.loadScenario(config);
        // Every activity is pinned to a link its person can actually use
        // BEFORE the Controler exists (DECISIONS.md 9.58): the router starts a
        // leg at the nearest link of the leg's mode while the qsim inserts the
        // vehicle at the activity's link, and with accessEgressType=none that
        // disagreement wedged ~11.6k walk/bike legs per iteration at a
        // disconnected first hop, aborting the agents mid-day.
        ActivityLinkAssigner.run(scenario);
        final Controler controler = new Controler(scenario);
        controler.addOverridingModule(new AbstractModule() {
            @Override
            public void install() {
                bind(PermissibleModesCalculator.class)
                        .to(AvailabilityModesCalculator.class);
                // The stock SubtourModeChoice's single-trip path
                // (probaForRandomSingleTripMode) never consults the
                // calculator bound above, so every per-person availability
                // rule was porous on half the mode innovations - measured as
                // 747 under-18 taxi trips at probe iteration 8 (DECISIONS.md
                // 9.84, #49/#50; the 9.15 class). The gated strategy refuses
                // an impermissible draw by reverting the one trip it changed;
                // when nothing is impermissible it changes nothing.
                addPlanStrategyBinding("SubtourModeChoice")
                        .toProvider(GatedSubtourModeChoice.class);
                // DECISIONS.md 9.121, #94: the PT router's direct walk is
                // evaluated on the walk network rather than the beeline the
                // raptor draws across the harbour. Both bindings only when
                // the declared basis (RUN.transit_router.direct_walk_basis,
                // emitted as ptDirectWalk.basis) asks for it; `beeline` is
                // the stock raptor untouched.
                if (ptDirectWalk.isNetwork()) {
                    // MATSim's injector requires explicit bindings: the stock
                    // raptor module's provider is injected by the wrapper and
                    // is bound nowhere else (measured: the first smoke died
                    // at injector creation on exactly this)
                    bind(ch.sbb.matsim.routing.pt.raptor
                            .SwissRailRaptorRoutingModuleProvider.class);
                    bind(ch.sbb.matsim.routing.pt.raptor.RaptorParametersForPerson.class)
                            .to(NetworkDirectWalkPtRouter.NoDirectWalkParameters.class)
                            .in(Singleton.class);
                    addRoutingModuleBinding(TransportMode.pt)
                            .toProvider(NetworkDirectWalkPtRouter.RouterProvider.class);
                }
                // #49 Tier C (DECISIONS.md 9.78): with pt-submode mapping a
                // passenger leg's mode is the scheduled bus/tram/rail/ferry,
                // and the stock DefaultAnalysisMainModeIdentifier either
                // mislabels the trip or throws outright - two distinct
                // submodes in one trip is an IllegalStateException, read
                // from the pinned jar's bytecode. The replacement folds the
                // declared transit modes back to `pt` for every main_mode
                // analysis (trips CSV, modestats), keeping the linked-trip
                // vocabulary identical on both sides of the switch; the
                // submode split is read from the boarded routes (Tier R),
                // never from this label. Under the aggregate representation
                // the fold is an identity map, so binding unconditionally
                // changes nothing there.
                bind(org.matsim.core.router.AnalysisMainModeIdentifier.class)
                        .to(PtSubmodeMainModeIdentifier.class);
                // Issue #28: without these, `ride` routes on free-flow times.
                addTravelTimeBinding(TransportMode.ride)
                        .to(networkTravelTime());
                addTravelDisutilityFactoryBinding(TransportMode.ride)
                        .to(carTravelDisutilityFactoryKey());
                // taxi (issue #49, 4.7.8): the same mechanism as ride - a
                // network-routed teleported mode inherits FREE-FLOW times
                // unless bound to the congested network travel time, and a
                // taxi that out-runs the traffic it rides in is #28's defect
                // with a meter. Bound only when the config's routing
                // vocabulary carries the mode, so a config without taxi
                // behaves exactly as before.
                if (config.routing().getNetworkModes().contains("taxi")) {
                    addTravelTimeBinding("taxi").to(networkTravelTime());
                    addTravelDisutilityFactoryBinding("taxi")
                            .to(carTravelDisutilityFactoryKey());
                }
                // Network-simulated unmotorised modes (DECISIONS.md 9.54):
                // the router's speed cap comes from the SAME vehicle type the
                // qsim loads, so estimate and physics cannot drift. Bound only
                // for modes the config actually runs in the qsim, so a config
                // without them behaves exactly as before.
                for (final String mode : new String[] {TransportMode.walk,
                                                       TransportMode.bike}) {
                    if (!config.qsim().getMainModes().contains(mode)) {
                        continue;
                    }
                    final org.matsim.vehicles.VehicleType type =
                            scenario.getVehicles().getVehicleTypes().get(
                                    org.matsim.api.core.v01.Id.create(
                                            mode,
                                            org.matsim.vehicles.VehicleType.class));
                    if (type == null) {
                        throw new IllegalStateException(
                                "qsim.mainMode contains '" + mode + "' but the "
                                + "vehicles file declares no such type; the "
                                + "speed cap is declared in the registry and "
                                + "emitted by build_matsim_run_inputs.py");
                    }
                    if (gradient.isLinkSpeed()) {
                        // Gradient in the ROUTER's estimate (DECISIONS.md
                        // 9.84): the same declared cap, times the same grade
                        // factor the qsim applies, from one shared formula -
                        // estimate and physics cannot drift.
                        addTravelTimeBinding(mode).toInstance(
                                new GradientLinkSpeed.Router(
                                        mode, type.getMaximumVelocity(),
                                        gradient));
                    } else {
                        addTravelTimeBinding(mode).toInstance(
                                new CappedSpeedTravelTime(
                                        type.getMaximumVelocity()));
                    }
                    if (TransportMode.bike.equals(mode)
                            && bikeStress.isFeltTime()) {
                        // Motor-traffic stress in the ROUTER's link cost
                        // (DECISIONS.md 9.138, #107): time x the stamped
                        // bike_stress_factor, so the route search prefers
                        // the quiet street. The SCORE half is installed
                        // below; under representation=absent this branch is
                        // never taken and the stock time-only factory stays.
                        addTravelDisutilityFactoryBinding(mode).toInstance(
                                new BikeStressDisutility.Factory(
                                        scenario.getNetwork()));
                    } else {
                        addTravelDisutilityFactoryBinding(mode).toInstance(
                                new org.matsim.core.router.costcalculators
                                        .OnlyTimeDependentTravelDisutilityFactory());
                    }
                }
            }
        });
        if (!parking.getPriceFile().isEmpty()) {
            controler.addOverridingModule(new AbstractModule() {
                @Override
                public void install() {
                    // One instance serving both roles: it accumulates as an
                    // event handler and emits as a controler listener.
                    bind(ParkingChargeHandler.class).in(Singleton.class);
                    addEventHandlerBinding().to(ParkingChargeHandler.class);
                    addControllerListenerBinding().to(ParkingChargeHandler.class);
                }
            });
        }
        if (ptFare.isEnabled()) {
            controler.addOverridingModule(new AbstractModule() {
                @Override
                public void install() {
                    // The published Opal fare on every pt journey
                    // (DECISIONS.md 9.135, #98): one instance in both roles,
                    // accumulating per-journey charges as an event handler
                    // and emitting the deferred PersonMoneyEvents as a
                    // controler listener - the ParkingChargeHandler
                    // discipline. Installed only when the emitted config
                    // carries the fare tables.
                    bind(PtFareChargeHandler.class).in(Singleton.class);
                    addEventHandlerBinding().to(PtFareChargeHandler.class);
                    addControllerListenerBinding().to(PtFareChargeHandler.class);
                }
            });
        }
        if (fare.isEnabled()) {
            controler.addOverridingModule(new AbstractModule() {
                @Override
                public void install() {
                    // The point-to-point flagfall (issue #49): one instance in
                    // both roles, accumulating per-departure charges as an
                    // event handler and emitting the deferred PersonMoneyEvents
                    // as a controler listener - the ParkingChargeHandler
                    // discipline. Installed only when the emitted config names
                    // a mode and a flagfall, so a config without the fare
                    // module behaves exactly as before.
                    bind(FareChargeHandler.class).in(Singleton.class);
                    addEventHandlerBinding().to(FareChargeHandler.class);
                    addControllerListenerBinding().to(FareChargeHandler.class);
                }
            });
        }
        // Taxi as a finite fleet (DECISIONS.md 9.99, issue #90). Installed
        // whenever the declared representation asks for it, independently of
        // the ride engine: the two constrain different modes and neither
        // implies the other. Like RidePairingEngine it acts at the
        // BeforeMobsim boundary, where every selected plan is stable - which
        // is why the fleet needs no mobsim engine, no dispatcher and no new
        // dependency, the MATSim DRT contrib being absent from this project's
        // pinned run stack and unreachable from its network sandbox.
        if (taxiFleet.isFleet()) {
            controler.addOverridingModule(new AbstractModule() {
                @Override
                public void install() {
                    bind(TaxiFleetEngine.class).in(Singleton.class);
                    addControllerListenerBinding().to(TaxiFleetEngine.class);
                }
            });
        }
        if (ridePairing.isEnabled()) {
            controler.addOverridingModule(new AbstractModule() {
                @Override
                public void install() {
                    // One instance in two roles: it accumulates the drivers'
                    // realised times as an event handler, and makes the pairing
                    // as a controler listener at the BeforeMobsim boundary.
                    bind(RidePairingEngine.class).in(Singleton.class);
                    addEventHandlerBinding().to(RidePairingEngine.class);
                    addControllerListenerBinding().to(RidePairingEngine.class);

                    // Escort and escorted are ONE journey (DECISIONS.md 9.82).
                    // Per-agent replanning splits the pair and cannot rejoin
                    // it; this offers the coherent plan back so the score can
                    // decide. Inert at escortCoherenceRate = 0.
                    bind(EscortCoherenceListener.class).in(Singleton.class);
                    addControllerListenerBinding()
                            .to(EscortCoherenceListener.class);
                }
            });
        }
        final boolean physicalBoarding =
                ridePairing.isEnabled() && ridePairing.isPhysicalBoarding();
        final boolean networkWalk =
                config.qsim().getMainModes().contains(TransportMode.walk);
        if (physicalBoarding || networkWalk) {
            controler.addOverridingQSimModule(new AbstractQSimModule() {
                @Override
                protected void configureQSim() {
                    if (physicalBoarding) {
                        // Physical boarding (DECISIONS.md 9.53, issue #48).
                        // The bookings it redeems live in the parent-scoped
                        // RidePairingEngine singleton bound above.
                        bind(JointRideEngine.class).asEagerSingleton();
                        addQSimComponentBinding(JointRideEngine.COMPONENT)
                                .to(JointRideEngine.class);
                    }
                    if (networkWalk) {
                        // Network-simulated walk (DECISIONS.md 9.54): the
                        // transit router's access/egress and direct-walk legs
                        // keep mode `walk` with a GENERIC route, and the stock
                        // agent source casts every main-mode leg's route to a
                        // NetworkRoute - measured to crash at agent insertion.
                        // The tolerant source parks vehicles only for
                        // network-routed legs, and the teleporter claims the
                        // generic ones at departure.
                        bind(GenericRouteTeleporter.class).asEagerSingleton();
                        addQSimComponentBinding(GenericRouteTeleporter.COMPONENT)
                                .to(GenericRouteTeleporter.class);
                        bind(TolerantAgentSource.class).asEagerSingleton();
                        // its own component name: component bindings COLLECT
                        // rather than override (measured - both sources ran
                        // and the walk vehicles were parked twice), so the
                        // stock source is removed from the components list
                        // below and this one added
                        addQSimComponentBinding("citysimTolerantAgentSource")
                                .to(TolerantAgentSource.class);
                    }
                }
            });
            // Departure handlers are consulted in component order, and the
            // teleportation engine claims EVERY departure that reaches it -
            // so the order is rebuilt explicitly: the generic-route teleporter
            // BEFORE the netsim engine (it claims only main-mode legs without
            // a network route), jointRide after the netsim (ride is not a
            // main mode) and before teleportation, teleportation last. A
            // missed boarding still falls through to Tier 1.
            controler.configureQSimComponents(components -> {
                components.removeNamedComponent(QNetsimEngineModule.COMPONENT_NAME);
                components.removeNamedComponent(TeleportationModule.COMPONENT_NAME);
                if (networkWalk) {
                    components.addNamedComponent(GenericRouteTeleporter.COMPONENT);
                }
                components.addNamedComponent(QNetsimEngineModule.COMPONENT_NAME);
                if (physicalBoarding) {
                    components.addNamedComponent(JointRideEngine.COMPONENT);
                }
                components.addNamedComponent(TeleportationModule.COMPONENT_NAME);
                if (networkWalk) {
                    components.removeNamedComponent(PopulationModule.COMPONENT_NAME);
                    components.addNamedComponent("citysimTolerantAgentSource");
                }
            });
        }
        if (gradient.isLinkSpeed()) {
            // Gradient in the MOBSIM's physics (DECISIONS.md 9.84). On the
            // non-signal stack the core's DefaultQNetworkFactory injects a
            // Multibinder<LinkSpeedCalculator> set, so the calculator is
            // ADDED to the default rather than replacing the factory. The
            // signals stack cannot be reached this way - its factory news
            // the delegate past Guice - and is wired in
            // CitysimSignalsControler with GradientSignalsNetworkFactory.
            controler.addOverridingQSimModule(new AbstractQSimModule() {
                @Override
                protected void configureQSim() {
                    com.google.inject.multibindings.Multibinder
                            .newSetBinder(binder(),
                                          org.matsim.core.mobsim.qsim
                                                  .qnetsimengine
                                                  .linkspeedcalculator
                                                  .LinkSpeedCalculator.class)
                            .addBinding()
                            .toInstance(new GradientLinkSpeed.Mobsim(gradient));
                }
            });
        }
        if (bikeStress.isFeltTime()) {
            controler.addOverridingModule(new AbstractModule() {
                @Override
                public void install() {
                    // The SCORE half of the bike stress channel (DECISIONS.md
                    // 9.138, #107): one instance in both roles, accumulating
                    // felt surplus seconds as an event handler and emitting
                    // the deferred PersonScoreEvents as a controler listener
                    // - the ParkingChargeHandler discipline.
                    bind(BikeStressScoring.class).in(Singleton.class);
                    addEventHandlerBinding().to(BikeStressScoring.class);
                    addControllerListenerBinding().to(BikeStressScoring.class);
                }
            });
        }
        if (incomeScoring.isEnabled()) {
            // Income-dependent money sensitivity (DECISIONS.md 9.138, #108):
            // MATSim core's own IndividualPersonScoringParameters, which
            // scales each person's marginalUtilityOfMoney by
            // (average income / personal income)^incomeExponent from the
            // `income` person attribute build_matsim_plans.py stamps. The
            // taste-variations parameter set that carries the exponent is
            // attached to every subpopulation's scoring parameters HERE,
            // from the declared registry values, rather than hand-written
            // into the emitted XML - one source, no drift. Subpopulations
            // that are volumes rather than budgets (external, freight) are
            // excluded by name; their agents carry no income attribute
            // either, so the exclusion is belt and braces.
            final java.util.Set<String> excluded = new java.util.HashSet<>();
            for (final String part
                    : incomeScoring.getExcludeSubpopulations().split(",")) {
                if (!part.trim().isEmpty()) {
                    excluded.add(part.trim());
                }
            }
            for (final org.matsim.core.config.groups.ScoringConfigGroup
                    .ScoringParameterSet sps
                    : config.scoring()
                            .getScoringParametersPerSubpopulation().values()) {
                final org.matsim.core.config.groups
                        .TasteVariationsConfigParameterSet tv =
                        sps.getOCreateTasteVariationsParams();
                tv.setIncomeExponent(incomeScoring.getIncomeExponent());
                tv.setExcludeSubpopulations(excluded);
            }
            controler.addOverridingModule(new AbstractModule() {
                @Override
                public void install() {
                    bind(org.matsim.core.scoring.functions
                            .ScoringParametersForPerson.class)
                            .to(org.matsim.core.scoring.functions
                                    .IndividualPersonScoringParameters.class)
                            .in(Singleton.class);
                }
            });
        }
        if (config.getModules().containsKey(TelemetryConfigGroup.NAME)) {
            controler.addOverridingModule(new AbstractModule() {
                @Override
                public void install() {
                    // One instance in three roles: it accumulates as an event
                    // handler, flushes live as a mobsim listener, and closes the
                    // iteration as a controler listener.
                    bind(RunTelemetry.class).in(Singleton.class);
                    addEventHandlerBinding().to(RunTelemetry.class);
                    addMobsimListenerBinding().to(RunTelemetry.class);
                    addControllerListenerBinding().to(RunTelemetry.class);
                }
            });
        }
        return controler;
    }
}
