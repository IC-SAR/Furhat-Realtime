package sar.furhat.realtime.states;

import sar.furhat.realtime.state.State;
import sar.furhat.realtime.subsystems.furhat_client.FurhatClient;

public class InitState extends State {
  private final FurhatClient furhatClient;
  
  public InitState(FurhatClient furhatClient) {
    this.furhatClient = furhatClient;
  }

  @Override
  public void enter() {
    furhatClient.connect();
  }
}
