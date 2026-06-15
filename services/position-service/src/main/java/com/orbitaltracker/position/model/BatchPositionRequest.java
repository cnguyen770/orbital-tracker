package com.orbitaltracker.position.model;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import jakarta.validation.Valid;
import java.util.List;

public record BatchPositionRequest(
        @NotEmpty(message = "satellites list is required")
        @Size(max = 1000, message = "batch size is capped at 1000 satellites")
        List<@Valid TleRequest> satellites,
        String timestamp
) {}
