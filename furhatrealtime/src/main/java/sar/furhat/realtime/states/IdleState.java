package sar.furhat.realtime.states;

import sar.furhat.realtime.state.State;
import sar.furhat.realtime.subsystems.furhat_client.FurhatClient;

public class IdleState extends State {
  private final FurhatClient furhatClient;

  public IdleState(FurhatClient furhatClient) {
    this.furhatClient = furhatClient;
  }

  
  
}
