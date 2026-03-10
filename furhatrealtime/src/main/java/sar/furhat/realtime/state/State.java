package sar.furhat.realtime.state;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;

public abstract class State {
  private boolean initialized;
  private final List<Transition> transitions = new ArrayList<>();

  /**
   * Enters the state when the state is initialized
   */
  public void enter() {

  }

  /**
   * Runs for every loop cycle
   */
  public void update() {

  }

  /**
   * Runs when the state is excited
   */
  public void exit() {

  }

  /**
   * Adds a transition for reason, and the next state. 
   * @param condition When this becomes true, the next state will be returned
   * @param nextState The state that you want to switch to
   * @return
   */
  public State addTransition(Supplier<Boolean> condition, State nextState) {
    transitions.add(new Transition(condition, nextState));
    return this;
  }

  /**
   * FOR THE STATE SCHEDULER
   * This checks if there is a state thats condition is true, if so, then this returns that state
   * @return
   */
  public State checkTransitions() {
    for (Transition transition : transitions) {
      if (transition.condition.get()) {
        return transition.nextState;
      }
    }
    return null;
  }

  /**
   * FOR THE STATE SCHEDULER
   * Ran when the state is setup
   */
  public final void initialize() {
    if (initialized) return;
    enter();
    initialized = true;
  }

  /**
   * Check if the state is initialized
   * @return
   */
  public boolean isInitialized() {
    return initialized;
  }

  private static class Transition {
    final Supplier<Boolean> condition;
    final State nextState;

    Transition(Supplier<Boolean> condition, State nextState) {
      this.condition = condition;
      this.nextState = nextState;
    }
  }
}
