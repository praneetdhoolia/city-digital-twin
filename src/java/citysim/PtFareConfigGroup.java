package citysim;

import java.util.Arrays;
import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;
import org.matsim.core.config.ReflectiveConfigGroup.Parameter;

/**
 * Declares the public transport fare schedule the run charges (DECISIONS.md
 * 9.135, issue #98). Every value here is EMITTED by the registry-driven config
 * builder from declared {@code A.fare.*} fields, themselves quoted verbatim
 * from the archived publication at {@code data/raw/fares/} — nothing in this
 * class or its consumer decides a number, and every default below is a
 * SENTINEL (empty or negative), never a value: a config that lost the binding
 * must refuse to run, not run on a number typed here (the ParkingConfigGroup
 * lesson, DECISIONS.md session record 2026-08-15).
 *
 * <p>Band grammar: {@code *BandsKm} holds the UPPER bound of each closed band
 * in km; the last band is open, so a fare list is always one longer than its
 * band list. The ferry carries no bands — the city's one crossing has a named
 * flat fare row in the publication.
 */
public final class PtFareConfigGroup extends ReflectiveConfigGroup {

    public static final String GROUP_NAME = "ptFare";

    @Parameter("trainBandsKm")
    public String trainBandsKm = "";
    @Parameter("trainAdultPeak")
    public String trainAdultPeak = "";
    @Parameter("trainAdultOffpeak")
    public String trainAdultOffpeak = "";
    @Parameter("trainChildPeak")
    public String trainChildPeak = "";
    @Parameter("trainChildOffpeak")
    public String trainChildOffpeak = "";
    @Parameter("busBandsKm")
    public String busBandsKm = "";
    @Parameter("busAdultPeak")
    public String busAdultPeak = "";
    @Parameter("busAdultOffpeak")
    public String busAdultOffpeak = "";
    @Parameter("busChildPeak")
    public String busChildPeak = "";
    @Parameter("busChildOffpeak")
    public String busChildOffpeak = "";
    @Parameter("tramBandsKm")
    public String tramBandsKm = "";
    @Parameter("tramAdultPeak")
    public String tramAdultPeak = "";
    @Parameter("tramAdultOffpeak")
    public String tramAdultOffpeak = "";
    @Parameter("tramChildPeak")
    public String tramChildPeak = "";
    @Parameter("tramChildOffpeak")
    public String tramChildOffpeak = "";
    @Parameter("ferryAdultPeak")
    public double ferryAdultPeak = -1.0;
    @Parameter("ferryAdultOffpeak")
    public double ferryAdultOffpeak = -1.0;
    @Parameter("ferryChildPeak")
    public double ferryChildPeak = -1.0;
    @Parameter("ferryChildOffpeak")
    public double ferryChildOffpeak = -1.0;
    @Parameter("seniorPerFareCap")
    public double seniorPerFareCap = -1.0;
    @Parameter("dailyCapAdult")
    public double dailyCapAdult = -1.0;
    @Parameter("dailyCapChild")
    public double dailyCapChild = -1.0;
    @Parameter("dailyCapSenior")
    public double dailyCapSenior = -1.0;
    @Parameter("transferDiscountAdult")
    public double transferDiscountAdult = -1.0;
    @Parameter("transferDiscountChild")
    public double transferDiscountChild = -1.0;
    @Parameter("transferWindowMin")
    public double transferWindowMin = -1.0;
    @Parameter("peakMorningStartH")
    public double peakMorningStartH = -1.0;
    @Parameter("peakMorningEndH")
    public double peakMorningEndH = -1.0;
    @Parameter("peakEveningStartH")
    public double peakEveningStartH = -1.0;
    @Parameter("peakEveningEndH")
    public double peakEveningEndH = -1.0;
    @Parameter("railPeakMorningStartH")
    public double railPeakMorningStartH = -1.0;
    @Parameter("offPeakAllDay")
    public boolean offPeakAllDay = false;
    @Parameter("childMinAge")
    public int childMinAge = -1;
    @Parameter("childMaxAge")
    public int childMaxAge = -1;
    @Parameter("seniorMinAge")
    public int seniorMinAge = -1;

    public PtFareConfigGroup() {
        super(GROUP_NAME);
    }

    public String getTrainBandsKm() {
        return this.trainBandsKm;
    }

    public String getTrainAdultPeak() {
        return this.trainAdultPeak;
    }

    public String getTrainAdultOffpeak() {
        return this.trainAdultOffpeak;
    }

    public String getTrainChildPeak() {
        return this.trainChildPeak;
    }

    public String getTrainChildOffpeak() {
        return this.trainChildOffpeak;
    }

    public String getBusBandsKm() {
        return this.busBandsKm;
    }

    public String getBusAdultPeak() {
        return this.busAdultPeak;
    }

    public String getBusAdultOffpeak() {
        return this.busAdultOffpeak;
    }

    public String getBusChildPeak() {
        return this.busChildPeak;
    }

    public String getBusChildOffpeak() {
        return this.busChildOffpeak;
    }

    public String getTramBandsKm() {
        return this.tramBandsKm;
    }

    public String getTramAdultPeak() {
        return this.tramAdultPeak;
    }

    public String getTramAdultOffpeak() {
        return this.tramAdultOffpeak;
    }

    public String getTramChildPeak() {
        return this.tramChildPeak;
    }

    public String getTramChildOffpeak() {
        return this.tramChildOffpeak;
    }

    public double getFerryAdultPeak() {
        return this.ferryAdultPeak;
    }

    public double getFerryAdultOffpeak() {
        return this.ferryAdultOffpeak;
    }

    public double getFerryChildPeak() {
        return this.ferryChildPeak;
    }

    public double getFerryChildOffpeak() {
        return this.ferryChildOffpeak;
    }

    public double getSeniorPerFareCap() {
        return this.seniorPerFareCap;
    }

    public double getDailyCapAdult() {
        return this.dailyCapAdult;
    }

    public double getDailyCapChild() {
        return this.dailyCapChild;
    }

    public double getDailyCapSenior() {
        return this.dailyCapSenior;
    }

    public double getTransferDiscountAdult() {
        return this.transferDiscountAdult;
    }

    public double getTransferDiscountChild() {
        return this.transferDiscountChild;
    }

    public double getTransferWindowMin() {
        return this.transferWindowMin;
    }

    public double getPeakMorningStartH() {
        return this.peakMorningStartH;
    }

    public double getPeakMorningEndH() {
        return this.peakMorningEndH;
    }

    public double getPeakEveningStartH() {
        return this.peakEveningStartH;
    }

    public double getPeakEveningEndH() {
        return this.peakEveningEndH;
    }

    public double getRailPeakMorningStartH() {
        return this.railPeakMorningStartH;
    }

    public boolean isOffPeakAllDay() {
        return this.offPeakAllDay;
    }

    public int getChildMinAge() {
        return this.childMinAge;
    }

    public int getChildMaxAge() {
        return this.childMaxAge;
    }

    public int getSeniorMinAge() {
        return this.seniorMinAge;
    }

    /** The module is live only when the emitter wrote a train fare table. */
    public boolean isEnabled() {
        return !this.trainAdultPeak.isEmpty();
    }

    /** Comma-separated doubles, the band/fare list encoding. */
    static double[] parse(final String csv) {
        if (csv.isEmpty()) {
            return new double[0];
        }
        return Arrays.stream(csv.split(","))
                .mapToDouble(s -> Double.parseDouble(s.trim())).toArray();
    }

    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!isEnabled()) {
            return;
        }
        checkTable("train", this.trainBandsKm, this.trainAdultPeak,
                this.trainAdultOffpeak, this.trainChildPeak,
                this.trainChildOffpeak);
        checkTable("bus", this.busBandsKm, this.busAdultPeak,
                this.busAdultOffpeak, this.busChildPeak,
                this.busChildOffpeak);
        checkTable("tram", this.tramBandsKm, this.tramAdultPeak,
                this.tramAdultOffpeak, this.tramChildPeak,
                this.tramChildOffpeak);
        final double[] scalars = {this.ferryAdultPeak,
                this.ferryAdultOffpeak, this.ferryChildPeak,
                this.ferryChildOffpeak, this.seniorPerFareCap,
                this.dailyCapAdult, this.dailyCapChild,
                this.dailyCapSenior, this.transferDiscountAdult,
                this.transferDiscountChild, this.transferWindowMin,
                this.peakMorningStartH, this.peakMorningEndH,
                this.peakEveningStartH, this.peakEveningEndH,
                this.railPeakMorningStartH};
        for (final double s : scalars) {
            if (s < 0.0) {
                throw new IllegalStateException(
                        "ptFare: a scalar is unset (sentinel -1); every value "
                        + "is emitted from the registry and a config that "
                        + "lost the binding must not run");
            }
        }
        if (this.childMinAge < 0 || this.childMaxAge < this.childMinAge
                || this.seniorMinAge <= this.childMaxAge) {
            throw new IllegalStateException(
                    "ptFare: age bounds unset or inconsistent");
        }
    }

    private static void checkTable(final String mode, final String bands,
            final String... fareLists) {
        final int nBands = parse(bands).length;
        for (final String fares : fareLists) {
            if (parse(fares).length != nBands + 1) {
                throw new IllegalStateException(
                        "ptFare: " + mode + " fare list must be one longer "
                        + "than its band list (last band open); got "
                        + parse(fares).length + " fares over " + nBands
                        + " bands");
            }
        }
    }
}
