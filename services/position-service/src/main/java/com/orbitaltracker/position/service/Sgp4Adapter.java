package com.orbitaltracker.position.service;

import org.springframework.stereotype.Component;
import sgp4.TLE;
import java.time.Instant;
import java.util.Date;

@Component
public class Sgp4Adapter {

    public double[] propagateTeme(String line1, String line2, Instant timestamp) {
        TLE tle = new TLE(line1, line2);

        Date epoch = tle.getEpoch();
        if (epoch == null) {
            return null;
        }

        double minutesAfterEpoch = (timestamp.toEpochMilli() - epoch.getTime()) / 60000.0;

        double[][] rv = tle.getRV(minutesAfterEpoch);

        if (tle.getSgp4Error() != 0) {
            return null;
        }

        return rv[0];
    }
}