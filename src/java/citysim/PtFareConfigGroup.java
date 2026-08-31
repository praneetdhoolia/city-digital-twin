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
    private String trainAdultPeakAud = "";
    private String trainAdultOffpeakAud = "";
    private String trainChildPeakAud = "";
    private String trainChildOffpeakAud = "";
    private String busBandsKm = "";
    private String busAdultPeakAud = "";
    private String busAdultOffpeakAud = "";
    private String busChildPeakAud = "";
    private String busChildOffpeakAud = "";
    private String tramBandsKm = "";
    private String tramAdultPeakAud = "";
    private String tramAdultOffpeakAud = "";
    private String tramChildPeakAud = "";
    private String tramChildOffpeakAud = "";
    private double ferryAdultPeakAud = -1.0;
    private double ferryAdultOffpeakAud = -1.0;
    private double ferryChildPeakAud = -1.0;
    private double ferryChildOffpeakAud = -1.0;
    private double seniorPerFareCapAud = -1.0;
    private double dailyCapAdultAud = -1.0;
    private double dailyCapChildAud = -1.0;
    private double dailyCapSeniorAud = -1.0;
    private double transferDiscountAdultAud = -1.0;
    private double transferDiscountChildAud = -1.0;
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

    @StringGetter("trainAdultPeakAud")
    public String getTrainAdultPeakAud() {
        return this.trainAdultPeakAud;
    }

    @StringSetter("trainAdultPeakAud")
    public void setTrainAdultPeakAud(final String v) {
        this.trainAdultPeakAud = v;
    }

    @StringGetter("trainAdultOffpeakAud")
    public String getTrainAdultOffpeakAud() {
        return this.trainAdultOffpeakAud;
    }

    @StringSetter("trainAdultOffpeakAud")
    public void setTrainAdultOffpeakAud(final String v) {
        this.trainAdultOffpeakAud = v;
    }

    @StringGetter("trainChildPeakAud")
    public String getTrainChildPeakAud() {
        return this.trainChildPeakAud;
    }

    @StringSetter("trainChildPeakAud")
    public void setTrainChildPeakAud(final String v) {
        this.trainChildPeakAud = v;
    }

    @StringGetter("trainChildOffpeakAud")
    public String getTrainChildOffpeakAud() {
        return this.trainChildOffpeakAud;
    }

    @StringSetter("trainChildOffpeakAud")
    public void setTrainChildOffpeakAud(final String v) {
        this.trainChildOffpeakAud = v;
    }

    @StringGetter("busBandsKm")
    public String getBusBandsKm() {
        return this.busBandsKm;
    }

    @StringSetter("busBandsKm")
    public void setBusBandsKm(final String v) {
        this.busBandsKm = v;
    }

    @StringGetter("busAdultPeakAud")
    public String getBusAdultPeakAud() {
        return this.busAdultPeakAud;
    }

    @StringSetter("busAdultPeakAud")
    public void setBusAdultPeakAud(final String v) {
        this.busAdultPeakAud = v;
    }

    @StringGetter("busAdultOffpeakAud")
    public String getBusAdultOffpeakAud() {
        return this.busAdultOffpeakAud;
    }

    @StringSetter("busAdultOffpeakAud")
    public void setBusAdultOffpeakAud(final String v) {
        this.busAdultOffpeakAud = v;
    }

    @StringGetter("busChildPeakAud")
    public String getBusChildPeakAud() {
        return this.busChildPeakAud;
    }

    @StringSetter("busChildPeakAud")
    public void setBusChildPeakAud(final String v) {
        this.busChildPeakAud = v;
    }

    @StringGetter("busChildOffpeakAud")
    public String getBusChildOffpeakAud() {
        return this.busChildOffpeakAud;
    }

    @StringSetter("busChildOffpeakAud")
    public void setBusChildOffpeakAud(final String v) {
        this.busChildOffpeakAud = v;
    }

    @StringGetter("tramBandsKm")
    public String getTramBandsKm() {
        return this.tramBandsKm;
    }

    @StringSetter("tramBandsKm")
    public void setTramBandsKm(final String v) {
        this.tramBandsKm = v;
    }

    @StringGetter("tramAdultPeakAud")
    public String getTramAdultPeakAud() {
        return this.tramAdultPeakAud;
    }

    @StringSetter("tramAdultPeakAud")
    public void setTramAdultPeakAud(final String v) {
        this.tramAdultPeakAud = v;
    }

    @StringGetter("tramAdultOffpeakAud")
    public String getTramAdultOffpeakAud() {
        return this.tramAdultOffpeakAud;
    }

    @StringSetter("tramAdultOffpeakAud")
    public void setTramAdultOffpeakAud(final String v) {
        this.tramAdultOffpeakAud = v;
    }

    @StringGetter("tramChildPeakAud")
    public String getTramChildPeakAud() {
        return this.tramChildPeakAud;
    }

    @StringSetter("tramChildPeakAud")
    public void setTramChildPeakAud(final String v) {
        this.tramChildPeakAud = v;
    }

    @StringGetter("tramChildOffpeakAud")
    public String getTramChildOffpeakAud() {
        return this.tramChildOffpeakAud;
    }

    @StringSetter("tramChildOffpeakAud")
    public void setTramChildOffpeakAud(final String v) {
        this.tramChildOffpeakAud = v;
    }

    @StringGetter("ferryAdultPeakAud")
    public double getFerryAdultPeakAud() {
        return this.ferryAdultPeakAud;
    }

    @StringSetter("ferryAdultPeakAud")
    public void setFerryAdultPeakAud(final double v) {
        this.ferryAdultPeakAud = v;
    }

    @StringGetter("ferryAdultOffpeakAud")
    public double getFerryAdultOffpeakAud() {
        return this.ferryAdultOffpeakAud;
    }

    @StringSetter("ferryAdultOffpeakAud")
    public void setFerryAdultOffpeakAud(final double v) {
        this.ferryAdultOffpeakAud = v;
    }

    @StringGetter("ferryChildPeakAud")
    public double getFerryChildPeakAud() {
        return this.ferryChildPeakAud;
    }

    @StringSetter("ferryChildPeakAud")
    public void setFerryChildPeakAud(final double v) {
        this.ferryChildPeakAud = v;
    }

    @StringGetter("ferryChildOffpeakAud")
    public double getFerryChildOffpeakAud() {
        return this.ferryChildOffpeakAud;
    }

    @StringSetter("ferryChildOffpeakAud")
    public void setFerryChildOffpeakAud(final double v) {
        this.ferryChildOffpeakAud = v;
    }

    @StringGetter("seniorPerFareCapAud")
    public double getSeniorPerFareCapAud() {
        return this.seniorPerFareCapAud;
    }

    @StringSetter("seniorPerFareCapAud")
    public void setSeniorPerFareCapAud(final double v) {
        this.seniorPerFareCapAud = v;
    }

    @StringGetter("dailyCapAdultAud")
    public double getDailyCapAdultAud() {
        return this.dailyCapAdultAud;
    }

    @StringSetter("dailyCapAdultAud")
    public void setDailyCapAdultAud(final double v) {
        this.dailyCapAdultAud = v;
    }

    @StringGetter("dailyCapChildAud")
    public double getDailyCapChildAud() {
        return this.dailyCapChildAud;
    }

    @StringSetter("dailyCapChildAud")
    public void setDailyCapChildAud(final double v) {
        this.dailyCapChildAud = v;
    }

    @StringGetter("dailyCapSeniorAud")
    public double getDailyCapSeniorAud() {
        return this.dailyCapSeniorAud;
    }

    @StringSetter("dailyCapSeniorAud")
    public void setDailyCapSeniorAud(final double v) {
        this.dailyCapSeniorAud = v;
    }

    @StringGetter("transferDiscountAdultAud")
    public double getTransferDiscountAdultAud() {
        return this.transferDiscountAdultAud;
    }

    @StringSetter("transferDiscountAdultAud")
    public void setTransferDiscountAdultAud(final double v) {
        this.transferDiscountAdultAud = v;
    }

    @StringGetter("transferDiscountChildAud")
    public double getTransferDiscountChildAud() {
        return this.transferDiscountChildAud;
    }

    @StringSetter("transferDiscountChildAud")
    public void setTransferDiscountChildAud(final double v) {
        this.transferDiscountChildAud = v;
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
        return !this.trainAdultPeakAud.isEmpty();
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
        checkTable("train", this.trainBandsKm, this.trainAdultPeakAud,
                this.trainAdultOffpeakAud, this.trainChildPeakAud,
                this.trainChildOffpeakAud);
        checkTable("bus", this.busBandsKm, this.busAdultPeakAud,
                this.busAdultOffpeakAud, this.busChildPeakAud,
                this.busChildOffpeakAud);
        checkTable("tram", this.tramBandsKm, this.tramAdultPeakAud,
                this.tramAdultOffpeakAud, this.tramChildPeakAud,
                this.tramChildOffpeakAud);
        final double[] scalars = {this.ferryAdultPeakAud,
                this.ferryAdultOffpeakAud, this.ferryChildPeakAud,
                this.ferryChildOffpeakAud, this.seniorPerFareCapAud,
                this.dailyCapAdultAud, this.dailyCapChildAud,
                this.dailyCapSeniorAud, this.transferDiscountAdultAud,
                this.transferDiscountChildAud, this.transferWindowMin,
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
