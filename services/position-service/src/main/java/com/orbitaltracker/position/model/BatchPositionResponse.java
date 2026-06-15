package com.orbitaltracker.position.model;

import java.util.List;

public record BatchPositionResponse(
        List<PositionResponse> positions,
        int count,
        String timestamp
) {}
