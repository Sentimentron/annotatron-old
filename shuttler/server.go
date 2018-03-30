package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"github.com/gorilla/websocket"
	"log"
	"net/http"
)

var addr = flag.String("addr", "localhost:10000", "HTTP Listening Address")
var upgrader = websocket.Upgrader{}

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

func HandleAuthenticationMessage(contents map[string]interface{}, conn *websocket.Conn) (interface{}, error) {
	var parsedMessage AuthenticationClientServerMessage
	err := ReinterpretMessage(contents, &parsedMessage)

	response := AuthenticationServerClientResponse{
		Response{"authentication"},
		false,
		false,
	}

	if err != nil {
		return response, err
	}

	// TODO: have to associate the connection with the token
	// TODO: connect to Annotatron backend
	// TODO: check the v1/hello API to validate
	// TODO: return
	return response, nil
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
	defer c.Close()
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
			response, err = HandleAuthenticationMessage(parsedMessage.Contents)
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
	// Start the front-end and back-end servers

	frontEndMux := http.NewServeMux()
	frontEndMux.Handle("/ws", ClientWithServerMessageHandler)

	//  backendMux := http.NewServeMux()
	//  backendMux.Handle("/ws", ServerMessageHandler)

	//  go func() {
	//    http.ListenAndServe("0.0.0.0:9001", backendMux)
	//  }()

	http.ListenAndServe("0.0.0.0:9002", frontEndMux)
}
