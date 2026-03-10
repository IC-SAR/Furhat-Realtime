package sar.furhat.realtime;


import sar.furhat.realtime.Constants.FurhatBase.Mode;

public class FurhatBase {
  private static FurhatBase instance = null;

  protected static Mode mode;

  private FurhatBase() {
    switch (mode) {
      case SIM:
        break;
      case REAL:
      default:
        break;
    }
  }

  public static synchronized FurhatBase getInstance() {
    if (instance == null) {
      instance = new FurhatBase();
    }
    return instance;
  }

  
}
