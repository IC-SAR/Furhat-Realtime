package sar.furhat.realtime;


import sar.furhat.realtime.Constants.FurhatBase.Mode;
import sar.furhat.realtime.subsystems.furhat_client.FurhatClient;

public class FurhatBase {
  private static FurhatBase instance = null;

  protected static Mode mode;
  private final FurhatClient furhatClient;

  private FurhatBase() {
    switch (mode) {
      case SIM:
        furhatClient = new FurhatClient(Constants.SimConstants.IP_ADDRESS, Constants.SimConstants.PORT_NUMBER);
        break;
      case REAL:
        furhatClient = new FurhatClient(Constants.RealConstants.IP_ADDRESS, Constants.RealConstants.PORT_NUMBER);
        break;
      default:
        furhatClient = null;
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
