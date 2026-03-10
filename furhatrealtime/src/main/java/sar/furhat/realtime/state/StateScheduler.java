package sar.furhat.realtime.state;


public class StateScheduler {
  private static StateScheduler instance = null;

  private static State currentState;
  private static boolean running = false;

  /**
   * Setups the state scheduler singleton
   * @return
   */
  public static synchronized StateScheduler Init() {
    if (instance == null) {
      instance = new StateScheduler();
    }
    return instance;
  }

  /**
   * Sets the current state being run
   * @param newState
   */
  public static void setState(State newState) {
    if (currentState != null) {
      currentState.exit();
    }

    currentState = newState;
    if (currentState != null) {
      currentState.initialize();
    }
  }

  /**
   * Updates every frame
   */
  private static void update() {
    if (currentState != null) {
      currentState.update();

      State nextState = currentState.checkTransitions();
      if (nextState != null) {
        setState(nextState);
      }
    }
  }

  public static void startLoop(long frameIntervalMs) {
    running = true;
    while (running) {
      update();
      try {
        Thread.sleep(frameIntervalMs);
      } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        break;
      }
    }
  }

  public static void stop() {
    running = false;
  }
}
