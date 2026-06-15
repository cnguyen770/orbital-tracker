package com.orbitaltracker.position.service;

import com.orbitaltracker.position.model.BatchPositionRequest;
import com.orbitaltracker.position.model.BatchPositionResponse;
import com.orbitaltracker.position.model.PositionResponse;
import com.orbitaltracker.position.model.TleRequest;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;

@Service
public class Sgp4Service {

    private static final double WGS84_A  = 6378.137;
    private static final double WGS84_F  = 1.0 / 298.257223563;
    private static final double WGS84_E2 = WGS84_F * (2.0 - WGS84_F);

    private final Sgp4Adapter adapter;

    public Sgp4Service(Sgp4Adapter adapter) {
        this.adapter = adapter;
    }

    public PositionResponse computePosition(TleRequest request) {
        Instant ts = parseTimestamp(request.timestamp());

        double[] teme = adapter.propagateTeme(request.tleLine1(), request.tleLine2(), ts);
        if (teme == null) {
            return null;
        }

        double jd = julianDate(ts);
        double[] ecef = temeToEcef(teme, jd);
        double[] geo  = ecefToGeodetic(ecef);

        return new PositionResponse(
                extractNoradId(request.tleLine1()),
                geo[0], geo[1], geo[2],
                ts.toString()
        );
    }

    public BatchPositionResponse computeBatch(BatchPositionRequest request) {
        Instant ts = parseTimestamp(request.timestamp());
        List<PositionResponse> results = new ArrayList<>(request.satellites().size());

        for (TleRequest sat : request.satellites()) {
            try {
                TleRequest withTimestamp = new TleRequest(sat.tleLine1(), sat.tleLine2(), ts.toString());
                PositionResponse pos = computePosition(withTimestamp);
                if (pos != null) {
                    results.add(pos);
                }
            } catch (Exception e) {
                // skip satellites that fail propagation
            }
        }

        return new BatchPositionResponse(results, results.size(), ts.toString());
    }

    private Instant parseTimestamp(String timestamp) {
        if (timestamp == null || timestamp.isBlank()) {
            return Instant.now();
        }
        try {
            return Instant.parse(timestamp);
        } catch (DateTimeParseException e) {
            throw new IllegalArgumentException(
                    "timestamp must be ISO-8601 (e.g. 2026-06-11T00:00:00Z)");
        }
    }

    public static String extractNoradId(String tleLine1) {
        if (tleLine1.length() < 7) {
            throw new IllegalArgumentException("TLE line 1 is too short");
        }
        return tleLine1.substring(2, 7).trim();
    }

    public static double julianDate(Instant instant) {
        return instant.toEpochMilli() / 86400000.0 + 2440587.5;
    }

    public static double gmst(double julianDate) {
        double degrees = 280.46061837 + 360.98564736629 * (julianDate - 2451545.0);
        degrees = degrees % 360.0;
        if (degrees < 0) degrees += 360.0;
        return Math.toRadians(degrees);
    }

    public static double[] temeToEcef(double[] teme, double julianDate) {
        double theta = gmst(julianDate);
        double cos   = Math.cos(theta);
        double sin   = Math.sin(theta);
        return new double[]{
                teme[0] * cos + teme[1] * sin,
               -teme[0] * sin + teme[1] * cos,
                teme[2]
        };
    }

    public static double[] ecefToGeodetic(double[] ecef) {
        double x = ecef[0];
        double y = ecef[1];
        double z = ecef[2];

        double lon = Math.atan2(y, x);
        double p   = Math.sqrt(x * x + y * y);
        double lat = Math.atan2(z, p * (1.0 - WGS84_E2));
        double alt = 0.0;

        for (int i = 0; i < 5; i++) {
            double sinLat = Math.sin(lat);
            double n      = WGS84_A / Math.sqrt(1.0 - WGS84_E2 * sinLat * sinLat);
            alt = p / Math.cos(lat) - n;
            lat = Math.atan2(z, p * (1.0 - WGS84_E2 * n / (n + alt)));
        }

        return new double[]{
                Math.toDegrees(lat),
                Math.toDegrees(lon),
                alt
        };
    }
}