package com.orbitaltracker.position.model;

import jakarta.validation.constraints.NotBlank;

public record TleRequest(
        @NotBlank(message = "tle_line1 is required") String tleLine1,
        @NotBlank(message = "tle_line2 is required") String tleLine2,
        String timestamp
) {}
