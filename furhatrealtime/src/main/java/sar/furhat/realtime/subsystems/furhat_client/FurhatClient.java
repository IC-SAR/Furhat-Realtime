package sar.furhat.realtime.subsystems.furhat_client;

import java.io.IOException;
import java.net.URI;
import java.util.concurrent.CountDownLatch;
import java.util.logging.Logger;

import jakarta.websocket.ClientEndpoint;
import jakarta.websocket.CloseReason;
import jakarta.websocket.ContainerProvider;
import jakarta.websocket.DeploymentException;
import jakarta.websocket.OnClose;
import jakarta.websocket.OnError;
import jakarta.websocket.OnOpen;
import jakarta.websocket.Session;
import jakarta.websocket.WebSocketContainer;
import sar.furhat.realtime.Main;

@ClientEndpoint
public class FurhatClient {
  private Logger logger;
  private Session session;

  private final String url;
  private final String ip;
  private final String port;
  private final CountDownLatch latch = new CountDownLatch(1);
  
  public FurhatClient(String ipAddress, String portNumber) {
    this.url = "ws://" + ipAddress + ":" + portNumber + "/api/events";
    this.ip = ipAddress;
    this.port = portNumber;

    logger = Logger.getLogger(Main.class.getName());
  }

  public void connect() {
    WebSocketContainer container = ContainerProvider.getWebSocketContainer();
    
    // try connecting to furhat
    try {
      container.connectToServer(this, URI.create(url));
    } catch (DeploymentException e) {
      System.err.println("Error deploying to robot: " + e.getMessage());
      logger.severe("Error deploying to robot");
    } catch (IOException e) {
      System.err.println("Error with IO: " + e.getMessage());
      logger.severe("Error connecting to robot with IO exception");
    }

    // wait
    try {
      logger.info("waiting for latch");
      latch.await();
      logger.info("wait completed for latch");
    } catch (InterruptedException e) {
      logger.warning("Error awaiting when connecting to robot");
    }

  }


  public void disconnect() {
    if (session == null) {
      logger.warning("Attempted disconnecting from robot, but there was no session");
      return;
    }

    try {
      session.close();
    } catch (IOException e) {
      logger.severe("Attempted disconnecting from robot, but there is a problem with the IO: " + e.getMessage());
    }
  }

  @OnOpen
  public void onOpen(Session session) {
    this.session = session;
    logger.info("Connected to robot at " + ip + ":" + port);
    latch.countDown();
  }

  @OnClose
  public void onClose(Session session, CloseReason reason) {
    logger.info("Disconnected from robot: " + reason);
  }

  @OnError
  public void OnError(Session session, Throwable error) {
    logger.severe("Error with robot: " + error.getMessage());
    error.printStackTrace();
  }
}
