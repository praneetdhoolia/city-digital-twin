import org.matsim.api.core.v01.Id;
import org.matsim.vehicles.*;
import org.matsim.core.mobsim.qsim.qnetsimengine.QVehicleImpl;

public class ModeVehicleProbe {
    public static void main(String[] args) {
        Vehicles vehicles = VehicleUtils.createVehiclesContainer();
        new MatsimVehicleReader(vehicles).readFile(args[0]);
        if (vehicles.getVehicleTypes().size() != 2) throw new AssertionError("type count");
        VehicleType compact = vehicles.getVehicleTypes().get(Id.create("compact", VehicleType.class));
        VehicleType cargo = vehicles.getVehicleTypes().get(Id.create("cargo", VehicleType.class));
        if (compact.getLength() != 3 || compact.getWidth() != 1.5 || cargo.getWidth() != 2.5)
            throw new AssertionError("body dimensions");
        if (!"compact".equals(compact.getNetworkMode())) throw new AssertionError("network mode");
        QVehicleImpl q = new QVehicleImpl(VehicleUtils.createVehicle(Id.createVehicleId("probe"), compact));
        if (q.getSizeInEquivalents() != 0.8 || q.getMaximumVelocity() != 15 || q.getPassengerCapacity() != 2)
            throw new AssertionError("qsim did not retain resolved values");
        QVehicleImpl freight = new QVehicleImpl(VehicleUtils.createVehicle(Id.createVehicleId("cargoProbe"), cargo));
        if (freight.getSizeInEquivalents() != 2 || freight.getMaximumVelocity() != 12 || freight.getPassengerCapacity() != 0)
            throw new AssertionError("zero passenger capacity or distinct cargo physics lost");
        System.out.println("PASS: MATSim reader and QVehicleImpl retain distinct bodies, PCE, speed caps and passenger capacities");
    }
}
