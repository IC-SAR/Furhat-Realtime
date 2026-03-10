package sar.furhat.realtime;

public final class Constants {
  public final static class FurhatBase {
    public enum Mode {
      SIM,
      REAL
    }
  }

  public final static class SimConstants {
    public static String IP_ADDRESS = "127.0.0.1";
    public static String PORT_NUMBER = "8080";
  }

  public final static class RealConstants {
    public static String IP_ADDRESS = "";
    public static String PORT_NUMBER = "9000";
  }
}
