package com.orbitaltracker.position.controller;

import com.orbitaltracker.position.model.BatchPositionRequest;
import com.orbitaltracker.position.model.BatchPositionResponse;
import com.orbitaltracker.position.model.PositionResponse;
import com.orbitaltracker.position.model.TleRequest;
import com.orbitaltracker.position.service.Sgp4Service;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class PositionController {

    private final Sgp4Service sgp4Service;

    public PositionController(Sgp4Service sgp4Service) {
        this.sgp4Service = sgp4Service;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok");
    }

    @PostMapping("/position")
    public PositionResponse position(@Valid @RequestBody TleRequest request) {
        return sgp4Service.computePosition(request);
    }

    @PostMapping("/positions/batch")
    public BatchPositionResponse batch(@Valid @RequestBody BatchPositionRequest request) {
        return sgp4Service.computeBatch(request);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Map<String, String> handleBadRequest(IllegalArgumentException e) {
        return Map.of("error", e.getMessage());
    }
}
