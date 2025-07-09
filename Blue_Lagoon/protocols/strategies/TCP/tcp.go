package TCP

import (
	"fmt"
	"net"
	"time"

	"github.com/mariocandela/beelzebub/v3/historystore"
	"github.com/mariocandela/beelzebub/v3/parser"
	"github.com/mariocandela/beelzebub/v3/plugins"
	"github.com/mariocandela/beelzebub/v3/tracer"

	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
)

type TCPStrategy struct {
	Sessions *historystore.HistoryStore
}

func (tcpStrategy *TCPStrategy) Init(servConf parser.BeelzebubServiceConfiguration, tr tracer.Tracer) error {
	if tcpStrategy.Sessions == nil {
		tcpStrategy.Sessions = historystore.NewHistoryStore()
	}
	go tcpStrategy.Sessions.HistoryCleaner() // Ensure cleaner is started, consistent with ssh.go

	listen, err := net.Listen("tcp", servConf.Address)
	if err != nil {
		log.Errorf("Error during init TCP Protocol: %s", err.Error())
		return err
	}

	go func() {
		for {
			if conn, err := listen.Accept(); err == nil {
				go func() {
					conn.SetDeadline(time.Now().Add(time.Duration(1000) * time.Second))
					conn.Write(fmt.Appendf([]byte{}, "%s\n", servConf.Banner))

					buffer := make([]byte, 1024)
					command := ""

					if n, err := conn.Read(buffer); err == nil {
						command = string(buffer[:n])
					}

					host, port, _ := net.SplitHostPort(conn.RemoteAddr().String())

					// If LLMProvider is configured, assume LLM plugin should be used for this TCP service.
					if servConf.Plugin.LLMProvider != "" {
						llmProvider, err := plugins.FromStringToLLMProvider(servConf.Plugin.LLMProvider)
						if err != nil {
							log.Errorf("Error parsing LLMProvider: %v. Falling back to default behavior.", err)
						} else {
							sessionKey := "TCP" + host // Using client IP for session key
							var histories []plugins.Message
							if tcpStrategy.Sessions.HasKey(sessionKey) {
								histories = tcpStrategy.Sessions.Query(sessionKey)
							}

							llmHoneypot := plugins.LLMHoneypot{
								Histories:    histories, // Pass conversation history
								OpenAIKey:    servConf.Plugin.OpenAISecretKey,
								Protocol:     tracer.TCP,
								Host:         servConf.Plugin.Host,
								Model:        servConf.Plugin.LLMModel,
								Provider:     llmProvider,
								CustomPrompt: servConf.Plugin.Prompt,
							}
							llmHoneypotInstance := plugins.InitLLMHoneypot(llmHoneypot)

							response, err := llmHoneypotInstance.ExecuteModel(command)
							if err != nil {
								log.Errorf("LLM ExecuteModel error for command '%s': %v. Falling back to default behavior.", command, err)
							} else {
								conn.Write([]byte(response))

								// Store interaction in history
								var newEntries []plugins.Message
								newEntries = append(newEntries, plugins.Message{Role: plugins.USER.String(), Content: command})
								newEntries = append(newEntries, plugins.Message{Role: plugins.ASSISTANT.String(), Content: response})
								tcpStrategy.Sessions.Append(sessionKey, newEntries...)
								// No need to update local 'histories' variable as the connection closes after one interaction for TCP
								tr.TraceEvent(tracer.Event{
									Msg:           "New TCP attempt (LLM)",
									Protocol:      tracer.TCP.String(),
									Command:       command,
									CommandOutput: response,
									Status:        tracer.Stateless.String(),
									RemoteAddr:    conn.RemoteAddr().String(),
									SourceIp:      host,
									SourcePort:    port,
									ID:            uuid.New().String(),
									Description:   servConf.Description,
									Handler:       plugins.LLMPluginName, // Using the constant for handler name
								})
								conn.Close()
								return // LLM interaction handled, return from goroutine
							}
						}
					}

					// Existing behavior if LLM is not configured for the service or if LLM interaction fails.
					tr.TraceEvent(tracer.Event{
						Msg:         "New TCP attempt",
						Protocol:    tracer.TCP.String(),
						Command:     command,
						Status:      tracer.Stateless.String(),
						RemoteAddr:  conn.RemoteAddr().String(),
						SourceIp:    host,
						SourcePort:  port,
						ID:          uuid.New().String(),
						Description: servConf.Description,
					})
					conn.Close()
				}()
			}
		}
	}()

	log.WithFields(log.Fields{
		"port":   servConf.Address,
		"banner": servConf.Banner,
	}).Infof("Init service %s", servConf.Protocol)
	return nil
}
