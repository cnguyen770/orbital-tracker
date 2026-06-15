package com.orbitaltracker.position.model;

public record PositionResponse(
        String noradId,
        double latitude,
        double longitude,
        double altitudeKm,
        String timestamp
) {}
