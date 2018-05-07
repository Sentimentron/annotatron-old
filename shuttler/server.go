package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"github.com/gorilla/websocket"
	"log"
	"net/http"
	"sync"
)

var addr = flag.String("addr", "localhost:10000", "HTTP Listening Address")
var upgrader = websocket.Upgrader{}

var connectionMapLock sync.Mutex // Synchronizes access to the connectionMap
var connectionMapId int          // Current insert point
var connectionMap map[int]*websocket.Conn
var connectionTokenMap map[int]string // Stores which connections belong to which users

// Message is the generic message type
type Message struct {
	Kind     string                 `json:"kind"`
	Contents map[string]interface{} `json:"payload"`
}

type Response struct {
	Kind string `json:"kind"`
}

// UnknownMessageServerClientResponse indicates that we couldn't handle the previous message
type UnhandledMessageServerClientResponse struct {
	Response
	Kind string `json:"unhandled_kind"`
}

// InternalErrorResponse indicates that something went wrong whilst processing the message
type InternalErrorResponse struct {
	Response
	Error string `json:"error"`
}

func CreateInternalErrorResponseFromError(err error) *InternalErrorResponse {
	ret := new(InternalErrorResponse)
	ret.Kind = "InternalError"
	ret.Error = fmt.Sprintf("%s", err)
	return ret
}

// AuthenticationClientServerMessage records the token the user's signed in with.
type AuthenticationClientServerMessage struct {
	Token string `json:"string"`
}

// AuthenticationServerClientResponse acknowledges whether the authentication token
// provided in the AuthenticationClientServerMessage is correct.
type AuthenticationServerClientResponse struct {
	Response
	Successful  bool `json:"sucessful"`
	RateLimited bool `json:"rate_limited"`
}

// ResourceUpdatedMessage indicates that a given class of resources have
// been updated and the client should refetch them.
type ResourceUpdatedMessage struct {
	ResourceKind string `json:"resource_kind"`
	OptionalId   uint64 `json:"optional_id"`
}

// ReinterpretMessage reinterprets the Contents field in Message to the type decided by Kind.
func ReinterpretMessage(contents map[string]interface{}, target interface{}) error {
	rawBytes, err := json.Marshal(contents)
	if err != nil {
		return err
	}
	err = json.Unmarshal(rawBytes, target)
	return err
}

func WriteMessageToSocket(response interface{}, conn *websocket.Conn, responseType int) error {
	rawBytes, err := json.Marshal(response)
	if err != nil {
		return err
	}
	err = conn.WriteMessage(responseType, rawBytes)
	return err
}

func HandleAuthenticationMessage(contents map[string]interface{}, conn *websocket.Conn) (interface{}, int, error) {
	var parsedMessage AuthenticationClientServerMessage
	err := ReinterpretMessage(contents, &parsedMessage)

	response := AuthenticationServerClientResponse{
		Response{"authentication"},
		false,
		false,
	}

	if err != nil {
		return response, 0, err
	}

	// TODO: have to associate the connection with the token
	// TODO: connect to Annotatron backend

	// Create a HTTP client and ping the check authentication method
	client := &http.Client{
		CheckRedirect: nil,
	}
	req, err := http.NewRequest("POST", "http://annotatron-service/v1/control/hello", nil)
	if err != nil {
		return response, 0, err
	}
	req.Header.Add("Authorization", fmt.Sprintf("Token %s", parsedMessage.Token))
	resp, err := client.Do(req)
	defer resp.Body.Close()
	if err != nil {
		return response, 0, err
	}

	// If successful (i.e. 200 status), stash the connection
	if resp.StatusCode == 200 {
		connectionId := RegisterConnection(conn, parsedMessage.Token)
		response.Successful = true
		return response, connectionId, nil
	}

	return response, 0, fmt.Errorf("status code was %d (expected 200)", resp.StatusCode)
}

// RegisterConnection adds the socket so that it can receive broadcast messages.
func RegisterConnection(c *websocket.Conn, token string) int {
	connectionMapLock.Lock()
	defer connectionMapLock.Unlock()
	connectionMapId += 1
	connectionMap[connectionMapId] = c
	connectionTokenMap[connectionMapId] = token
	return connectionMapId
}

// DeregisterAndCloseConnection removes the connection from the connectionMap (if it exists)
// and also closes the connection.
func DeregisterAndCloseConnection(c *websocket.Conn, connectionId *int) {
	if _, ok := connectionMap[*connectionId]; ok {
		connectionMapLock.Lock()
		defer connectionMapLock.Unlock()
		delete(connectionMap, *connectionId)
		delete(connectionTokenMap, *connectionId)
	}
	c.Close()
}

// ClientWithServerMessageHandler handles the frontend connection - the Vue.JS app
// connects to this endpoint to authenticate and receive updates.
// TODO: integrate with connection map
func ClientWithServerMessageHandler(w http.ResponseWriter, r *http.Request) {
	// Configure and upgrade the connection
	c, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Print("Failed to upgrade HTTP connection: ", err)
		return
	}
	connectionId := 0 // Deliberately set to something that's not in the connectionMap
	defer DeregisterAndCloseConnection(c, &connectionId)
	for {
		// Read the raw bytes from the socket
		mt, message, err := c.ReadMessage()
		if err != nil {
			log.Println("Failed to read from socket: ", err)
			break
		}
		// Parse the message
		var parsedMessage Message
		unhandled := UnhandledMessageServerClientResponse{Kind: "unknown"}

		err = json.Unmarshal(message, &parsedMessage)
		if err != nil {
			log.Println("Failed to parse message: ", err)
			WriteMessageToSocket(unhandled, c, mt)
			return
		}

		var response interface{}

		switch kind := parsedMessage.Kind; kind {
		case "authentication":
			response, connectionId, err = HandleAuthenticationMessage(parsedMessage.Contents, c)
		default:
			unhandled.Kind = parsedMessage.Kind
			response = unhandled
		}

		shouldClose := false
		if err != nil {
			log.Println("Error occurred: ", err)
			response = CreateInternalErrorResponseFromError(err)
		}

		err = WriteMessageToSocket(response, c, mt)
		if err != nil {
			log.Println("ERROR_WRITING:", err)
			shouldClose = true
		}
		if shouldClose {
			return
		}
	}
}

func main() {

	// Create a map of sockets connected to this system, used for server broadcasts
	connectionMap = make(map[int]*websocket.Conn)
	connectionTokenMap = make(map[int]string)

	// Start the front-end and back-end servers
	frontEndMux := http.NewServeMux()
	frontEndMux.HandleFunc("/ws", ClientWithServerMessageHandler)

	//  backendMux := http.NewServeMux()
	//  backendMux.Handle("/ws", ServerMessageHandler)

	//  go func() {
	//    http.ListenAndServe("0.0.0.0:9001", backendMux)
	//  }()

	http.ListenAndServe("0.0.0.0:9002", frontEndMux)
}
