package citysim;

import java.util.Arrays;
import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

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

    private String trainBandsKm = "";
    private String trainAdultPeak = "";
    private String trainAdultOffpeak = "";
    private String trainChildPeak = "";
    private String trainChildOffpeak = "";
    private String busBandsKm = "";
    private String busAdultPeak = "";
    private String busAdultOffpeak = "";
    private String busChildPeak = "";
    private String busChildOffpeak = "";
    private String tramBandsKm = "";
    private String tramAdultPeak = "";
    private String tramAdultOffpeak = "";
    private String tramChildPeak = "";
    private String tramChildOffpeak = "";
    private double ferryAdultPeak = -1.0;
    private double ferryAdultOffpeak = -1.0;
    private double ferryChildPeak = -1.0;
    private double ferryChildOffpeak = -1.0;
    private double seniorPerFareCap = -1.0;
    private double dailyCapAdult = -1.0;
    private double dailyCapChild = -1.0;
    private double dailyCapSenior = -1.0;
    private double transferDiscountAdult = -1.0;
    private double transferDiscountChild = -1.0;
    private double transferWindowMin = -1.0;
    private double peakMorningStartH = -1.0;
    private double peakMorningEndH = -1.0;
    private double peakEveningStartH = -1.0;
    private double peakEveningEndH = -1.0;
    private double railPeakMorningStartH = -1.0;
    private boolean offPeakAllDay = false;
    private int childMinAge = -1;
    private int childMaxAge = -1;
    private int seniorMinAge = -1;

    public PtFareConfigGroup() {
        super(GROUP_NAME);
    }

    @StringGetter("trainBandsKm")
    public String getTrainBandsKm() {
        return this.trainBandsKm;
    }

    @StringSetter("trainBandsKm")
    public void setTrainBandsKm(final String v) {
        this.trainBandsKm = v;
    }

    @StringGetter("trainAdultPeak")
    public String getTrainAdultPeak() {
        return this.trainAdultPeak;
    }

    @StringSetter("trainAdultPeak")
    public void setTrainAdultPeak(final String v) {
        this.trainAdultPeak = v;
    }

    @StringGetter("trainAdultOffpeak")
    public String getTrainAdultOffpeak() {
        return this.trainAdultOffpeak;
    }

    @StringSetter("trainAdultOffpeak")
    public void setTrainAdultOffpeak(final String v) {
        this.trainAdultOffpeak = v;
    }

    @StringGetter("trainChildPeak")
    public String getTrainChildPeak() {
        return this.trainChildPeak;
    }

    @StringSetter("trainChildPeak")
    public void setTrainChildPeak(final String v) {
        this.trainChildPeak = v;
    }

    @StringGetter("trainChildOffpeak")
    public String getTrainChildOffpeak() {
        return this.trainChildOffpeak;
    }

    @StringSetter("trainChildOffpeak")
    public void setTrainChildOffpeak(final String v) {
        this.trainChildOffpeak = v;
    }

    @StringGetter("busBandsKm")
    public String getBusBandsKm() {
        return this.busBandsKm;
    }

    @StringSetter("busBandsKm")
    public void setBusBandsKm(final String v) {
        this.busBandsKm = v;
    }

    @StringGetter("busAdultPeak")
    public String getBusAdultPeak() {
        return this.busAdultPeak;
    }

    @StringSetter("busAdultPeak")
    public void setBusAdultPeak(final String v) {
        this.busAdultPeak = v;
    }

    @StringGetter("busAdultOffpeak")
    public String getBusAdultOffpeak() {
        return this.busAdultOffpeak;
    }

    @StringSetter("busAdultOffpeak")
    public void setBusAdultOffpeak(final String v) {
        this.busAdultOffpeak = v;
    }

    @StringGetter("busChildPeak")
    public String getBusChildPeak() {
        return this.busChildPeak;
    }

    @StringSetter("busChildPeak")
    public void setBusChildPeak(final String v) {
        this.busChildPeak = v;
    }

    @StringGetter("busChildOffpeak")
    public String getBusChildOffpeak() {
        return this.busChildOffpeak;
    }

    @StringSetter("busChildOffpeak")
    public void setBusChildOffpeak(final String v) {
        this.busChildOffpeak = v;
    }

    @StringGetter("tramBandsKm")
    public String getTramBandsKm() {
        return this.tramBandsKm;
    }

    @StringSetter("tramBandsKm")
    public void setTramBandsKm(final String v) {
        this.tramBandsKm = v;
    }

    @StringGetter("tramAdultPeak")
    public String getTramAdultPeak() {
        return this.tramAdultPeak;
    }

    @StringSetter("tramAdultPeak")
    public void setTramAdultPeak(final String v) {
        this.tramAdultPeak = v;
    }

    @StringGetter("tramAdultOffpeak")
    public String getTramAdultOffpeak() {
        return this.tramAdultOffpeak;
    }

    @StringSetter("tramAdultOffpeak")
    public void setTramAdultOffpeak(final String v) {
        this.tramAdultOffpeak = v;
    }

    @StringGetter("tramChildPeak")
    public String getTramChildPeak() {
        return this.tramChildPeak;
    }

    @StringSetter("tramChildPeak")
    public void setTramChildPeak(final String v) {
        this.tramChildPeak = v;
    }

    @StringGetter("tramChildOffpeak")
    public String getTramChildOffpeak() {
        return this.tramChildOffpeak;
    }

    @StringSetter("tramChildOffpeak")
    public void setTramChildOffpeak(final String v) {
        this.tramChildOffpeak = v;
    }

    @StringGetter("ferryAdultPeak")
    public double getFerryAdultPeak() {
        return this.ferryAdultPeak;
    }

    @StringSetter("ferryAdultPeak")
    public void setFerryAdultPeak(final double v) {
        this.ferryAdultPeak = v;
    }

    @StringGetter("ferryAdultOffpeak")
    public double getFerryAdultOffpeak() {
        return this.ferryAdultOffpeak;
    }

    @StringSetter("ferryAdultOffpeak")
    public void setFerryAdultOffpeak(final double v) {
        this.ferryAdultOffpeak = v;
    }

    @StringGetter("ferryChildPeak")
    public double getFerryChildPeak() {
        return this.ferryChildPeak;
    }

    @StringSetter("ferryChildPeak")
    public void setFerryChildPeak(final double v) {
        this.ferryChildPeak = v;
    }

    @StringGetter("ferryChildOffpeak")
    public double getFerryChildOffpeak() {
        return this.ferryChildOffpeak;
    }

    @StringSetter("ferryChildOffpeak")
    public void setFerryChildOffpeak(final double v) {
        this.ferryChildOffpeak = v;
    }

    @StringGetter("seniorPerFareCap")
    public double getSeniorPerFareCap() {
        return this.seniorPerFareCap;
    }

    @StringSetter("seniorPerFareCap")
    public void setSeniorPerFareCap(final double v) {
        this.seniorPerFareCap = v;
    }

    @StringGetter("dailyCapAdult")
    public double getDailyCapAdult() {
        return this.dailyCapAdult;
    }

    @StringSetter("dailyCapAdult")
    public void setDailyCapAdult(final double v) {
        this.dailyCapAdult = v;
    }

    @StringGetter("dailyCapChild")
    public double getDailyCapChild() {
        return this.dailyCapChild;
    }

    @StringSetter("dailyCapChild")
    public void setDailyCapChild(final double v) {
        this.dailyCapChild = v;
    }

    @StringGetter("dailyCapSenior")
    public double getDailyCapSenior() {
        return this.dailyCapSenior;
    }

    @StringSetter("dailyCapSenior")
    public void setDailyCapSenior(final double v) {
        this.dailyCapSenior = v;
    }

    @StringGetter("transferDiscountAdult")
    public double getTransferDiscountAdult() {
        return this.transferDiscountAdult;
    }

    @StringSetter("transferDiscountAdult")
    public void setTransferDiscountAdult(final double v) {
        this.transferDiscountAdult = v;
    }

    @StringGetter("transferDiscountChild")
    public double getTransferDiscountChild() {
        return this.transferDiscountChild;
    }

    @StringSetter("transferDiscountChild")
    public void setTransferDiscountChild(final double v) {
        this.transferDiscountChild = v;
    }

    @StringGetter("transferWindowMin")
    public double getTransferWindowMin() {
        return this.transferWindowMin;
    }

    @StringSetter("transferWindowMin")
    public void setTransferWindowMin(final double v) {
        this.transferWindowMin = v;
    }

    @StringGetter("peakMorningStartH")
    public double getPeakMorningStartH() {
        return this.peakMorningStartH;
    }

    @StringSetter("peakMorningStartH")
    public void setPeakMorningStartH(final double v) {
        this.peakMorningStartH = v;
    }

    @StringGetter("peakMorningEndH")
    public double getPeakMorningEndH() {
        return this.peakMorningEndH;
    }

    @StringSetter("peakMorningEndH")
    public void setPeakMorningEndH(final double v) {
        this.peakMorningEndH = v;
    }

    @StringGetter("peakEveningStartH")
    public double getPeakEveningStartH() {
        return this.peakEveningStartH;
    }

    @StringSetter("peakEveningStartH")
    public void setPeakEveningStartH(final double v) {
        this.peakEveningStartH = v;
    }

    @StringGetter("peakEveningEndH")
    public double getPeakEveningEndH() {
        return this.peakEveningEndH;
    }

    @StringSetter("peakEveningEndH")
    public void setPeakEveningEndH(final double v) {
        this.peakEveningEndH = v;
    }

    @StringGetter("railPeakMorningStartH")
    public double getRailPeakMorningStartH() {
        return this.railPeakMorningStartH;
    }

    @StringSetter("railPeakMorningStartH")
    public void setRailPeakMorningStartH(final double v) {
        this.railPeakMorningStartH = v;
    }

    @StringGetter("offPeakAllDay")
    public boolean isOffPeakAllDay() {
        return this.offPeakAllDay;
    }

    @StringSetter("offPeakAllDay")
    public void setOffPeakAllDay(final boolean v) {
        this.offPeakAllDay = v;
    }

    @StringGetter("childMinAge")
    public int getChildMinAge() {
        return this.childMinAge;
    }

    @StringSetter("childMinAge")
    public void setChildMinAge(final int v) {
        this.childMinAge = v;
    }

    @StringGetter("childMaxAge")
    public int getChildMaxAge() {
        return this.childMaxAge;
    }

    @StringSetter("childMaxAge")
    public void setChildMaxAge(final int v) {
        this.childMaxAge = v;
    }

    @StringGetter("seniorMinAge")
    public int getSeniorMinAge() {
        return this.seniorMinAge;
    }

    @StringSetter("seniorMinAge")
    public void setSeniorMinAge(final int v) {
        this.seniorMinAge = v;
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
