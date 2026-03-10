package sar.furhat.realtime;

import java.util.logging.Logger;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

import sar.furhat.realtime.Constants.FurhatBase.Mode;

public class Main {
    public static void main(String[] args) {
        Logger logger = Logger.getLogger(Main.class.getName());

        Options options = new Options();
        options.addOption("s", "sim", false, "Run in simulation mode");
        options.addOption("m", "mode", true, "Mode to run");
        
        CommandLineParser parser = new DefaultParser();
        CommandLine cmd;
        try {
            cmd = parser.parse(options, args);
        } catch (ParseException e) {
            System.err.println("Error parsing arguments: " + e.getMessage());
            logger.severe("Error parsing arguments: \" + e.getMessage())");
            return;
        }

        if (cmd.hasOption("mode")) {
            String modeVal = cmd.getOptionValue("mode");
            if (modeVal.equalsIgnoreCase("sim")) {
                FurhatBase.setMode(Mode.SIM);
                logger.config("Requested Mode: sim");
            } else if (modeVal.equalsIgnoreCase("real")) {
                FurhatBase.setMode(Mode.REAL);
                logger.config("Requested Mode: sim");
            } 
        } else {
            FurhatBase.setMode(Mode.REAL);
            logger.config("Requested Mode: N/A. Falling back to REAL");
        }

        FurhatBase.Init();


    }

}