package com.orbitaltracker.position;

import com.orbitaltracker.position.controller.PositionController;
import com.orbitaltracker.position.model.PositionResponse;
import com.orbitaltracker.position.service.Sgp4Service;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(PositionController.class)
class PositionControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private Sgp4Service sgp4Service;

    @Test
    void healthReturnsOk() throws Exception {
        mockMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("ok"));
    }

    @Test
    void positionWithValidTleReturnsComputedResult() throws Exception {
        when(sgp4Service.computePosition(any())).thenReturn(
                new PositionResponse("25544", 51.5, -0.1, 420.0, "2026-06-11T00:00:00Z"));

        String body = """
                {
                  "tleLine1": "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9000",
                  "tleLine2": "2 25544  51.6400 208.9163 0006317  69.9862  25.2906 15.49560532428342"
                }
                """;

        mockMvc.perform(post("/position").contentType(APPLICATION_JSON).content(body))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.noradId").value("25544"))
                .andExpect(jsonPath("$.latitude").value(51.5))
                .andExpect(jsonPath("$.altitudeKm").value(420.0));
    }

    @Test
    void positionWithMissingTleLineIsRejected() throws Exception {
        String body = """
                { "tleLine1": "", "tleLine2": "2 25544  51.6400 ..." }
                """;

        mockMvc.perform(post("/position").contentType(APPLICATION_JSON).content(body))
                .andExpect(status().isBadRequest());
    }

    @Test
    void batchWithEmptyListIsRejected() throws Exception {
        String body = """
                { "satellites": [] }
                """;

        mockMvc.perform(post("/positions/batch").contentType(APPLICATION_JSON).content(body))
                .andExpect(status().isBadRequest());
    }
}
