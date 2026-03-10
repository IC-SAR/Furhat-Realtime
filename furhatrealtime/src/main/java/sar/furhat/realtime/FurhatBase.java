package sar.furhat.realtime;


import sar.furhat.realtime.Constants.FurhatBase.Mode;
import sar.furhat.realtime.state.StateScheduler;
import sar.furhat.realtime.states.InitState;
import sar.furhat.realtime.subsystems.furhat_client.FurhatClient;

public class FurhatBase {
  private static FurhatBase instance = null;

  private static Mode mode;
  private final FurhatClient furhatClient;
  private final InitState initState;

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

    initState = new InitState(furhatClient);
    StateScheduler.setState(initState);
    StateScheduler.startLoop(0);
  }

  public static synchronized FurhatBase Init() {
    if (instance == null) {
      instance = new FurhatBase();
    }
    return instance;
  }

  public static synchronized void setMode(Mode mode) {
    FurhatBase.mode = mode;
  }
}
