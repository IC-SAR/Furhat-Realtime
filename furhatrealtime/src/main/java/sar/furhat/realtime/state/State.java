package sar.furhat.realtime.state;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;

public abstract class State {
  private boolean initialized;
  private final List<Transition> transitions = new ArrayList<>();

  public void enter() {

  }

  public void update() {

  }

  public void exit() {

  }

  public State addTransition(Supplier<Boolean> condition, State nextState) {
    transitions.add(new Transition(condition, nextState));
    return this;
  }

  public State checkTransitions() {
    for (Transition transition : transitions) {
      if (transition.condition.get()) {
        return transition.nextState;
      }
    }
    return null;
  }

  public final void initialize() {
    if (initialized) return;
    enter();
    initialized = true;
  }

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
