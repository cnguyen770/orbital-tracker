package com.orbitaltracker.position;

import com.orbitaltracker.position.service.Sgp4Service;
import org.junit.jupiter.api.Test;

import java.time.Instant;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class Sgp4ServiceTest {

    @Test
    void julianDateAtUnixEpoch() {
        double jd = Sgp4Service.julianDate(Instant.parse("1970-01-01T00:00:00Z"));
        assertEquals(2440587.5, jd, 1e-9);
    }

    @Test
    void julianDateAtJ2000() {
        double jd = Sgp4Service.julianDate(Instant.parse("2000-01-01T12:00:00Z"));
        assertEquals(2451545.0, jd, 1e-9);
    }

    @Test
    void gmstAtJ2000MatchesReference() {
        double theta = Math.toDegrees(Sgp4Service.gmst(2451545.0));
        assertEquals(280.46061837, theta, 1e-6);
    }

    @Test
    void ecefOnEquatorAtPrimeMeridian() {
        double[] geo = Sgp4Service.ecefToGeodetic(new double[]{6778.137, 0.0, 0.0});
        assertEquals(0.0, geo[0], 1e-6);
        assertEquals(0.0, geo[1], 1e-6);
        assertEquals(400.0, geo[2], 1e-3);
    }

    @Test
    void ecefAtNinetyDegreesEast() {
        double[] geo = Sgp4Service.ecefToGeodetic(new double[]{0.0, 6778.137, 0.0});
        assertEquals(0.0, geo[0], 1e-6);
        assertEquals(90.0, geo[1], 1e-6);
        assertEquals(400.0, geo[2], 1e-3);
    }

    @Test
    void temeToEcefIsPureRotationAtZeroGmst() {
        double[] teme = new double[]{4000.0, 3000.0, 2000.0};
        double[] ecef = Sgp4Service.temeToEcef(teme, 2460000.0);
        double lenTeme = Math.sqrt(teme[0] * teme[0] + teme[1] * teme[1] + teme[2] * teme[2]);
        double lenEcef = Math.sqrt(ecef[0] * ecef[0] + ecef[1] * ecef[1] + ecef[2] * ecef[2]);
        assertEquals(lenTeme, lenEcef, 1e-9);
        assertEquals(teme[2], ecef[2], 1e-9);
    }

    @Test
    void extractNoradIdFromIssTle() {
        String line1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9000";
        assertEquals("25544", Sgp4Service.extractNoradId(line1));
    }

    @Test
    void extractNoradIdRejectsShortLine() {
        assertThrows(IllegalArgumentException.class,
                () -> Sgp4Service.extractNoradId("1 25"));
    }
}
