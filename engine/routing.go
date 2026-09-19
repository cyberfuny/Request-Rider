package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"strings"
	"sync"
	"time"

	xproxy "golang.org/x/net/proxy"
)

type routeConfig struct {
	Address string `json:"address"`
}

type routeManager struct {
	mu     sync.RWMutex
	config routeConfig
	dialer func(context.Context, string, string) (net.Conn, error)
}

func newRouteManager() (*routeManager, error) {
	manager := &routeManager{}
	if err := manager.set(routeConfig{}); err != nil {
		return nil, err
	}
	return manager, nil
}

func (m *routeManager) set(config routeConfig) error {
	address := strings.TrimSpace(config.Address)
	if address == "" {
		directDialer := &net.Dialer{
			Timeout:   10 * time.Second,
			KeepAlive: 30 * time.Second,
		}
		m.mu.Lock()
		m.config = routeConfig{}
		m.dialer = directDialer.DialContext
		m.mu.Unlock()
		return nil
	}

	socksDialer, err := xproxy.SOCKS5("tcp", address, nil, &net.Dialer{
		Timeout:   10 * time.Second,
		KeepAlive: 30 * time.Second,
	})
	if err != nil {
		return fmt.Errorf("configure SOCKS5 route %s: %w", address, err)
	}
	dial := func(ctx context.Context, network, target string) (net.Conn, error) {
		type result struct {
			conn net.Conn
			err  error
		}
		results := make(chan result, 1)
		go func() {
			conn, err := socksDialer.Dial(network, target)
			results <- result{conn: conn, err: err}
		}()
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case result := <-results:
			return result.conn, result.err
		}
	}

	m.mu.Lock()
	m.config = routeConfig{Address: address}
	m.dialer = dial
	m.mu.Unlock()
	return nil
}

func (m *routeManager) configSnapshot() routeConfig {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.config
}

func (m *routeManager) dialContext(ctx context.Context, network, target string) (net.Conn, error) {
	m.mu.RLock()
	dial := m.dialer
	m.mu.RUnlock()
	if dial == nil {
		return nil, fmt.Errorf("route is not configured")
	}
	return dial(ctx, network, target)
}

func (m *routeManager) transport() *http.Transport {
	return &http.Transport{
		Proxy:                 nil,
		DialContext:           m.dialContext,
		ForceAttemptHTTP2:     true,
		MaxIdleConns:          100,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,
		ResponseHeaderTimeout: 30 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
	}
}
