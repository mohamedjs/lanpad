import React, { useState, useEffect, useRef } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  TextInput,
  Modal,
  SafeAreaView,
  PanResponder,
  Platform,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { connect, disconnect, sendEvents, setStatusListener } from './src/sender';

export default function App() {
  const [host, setHost] = useState('192.168.1.225');
  const [port, setPort] = useState('8765');
  const [token, setToken] = useState('');
  const [status, setStatus] = useState('disconnected');
  const [rtt, setRtt] = useState(0);
  const [modalVisible, setModalVisible] = useState(false);
  const [textInput, setTextInput] = useState('');

  const lastPos = useRef({ x: 0, y: 0 });
  const touchStartTime = useRef(0);
  const touchStartPos = useRef({ x: 0, y: 0 });

  useEffect(() => {
    setStatusListener((newStatus, newRtt) => {
      setStatus(newStatus);
      setRtt(newRtt);
    });
    // Auto-connect if token present
    if (token) {
      connect(host, port, token);
    } else {
      setModalVisible(true);
    }
  }, []);

  const handleConnect = () => {
    connect(host, port, token);
    setModalVisible(false);
  };

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,

      onPanResponderGrant: (evt) => {
        const { touches } = evt.nativeEvent;
        touchStartTime.current = Date.now();
        if (touches.length === 1) {
          lastPos.current = { x: touches[0].pageX, y: touches[0].pageY };
          touchStartPos.current = { x: touches[0].pageX, y: touches[0].pageY };
        } else if (touches.length === 2) {
          lastPos.current = {
            x: (touches[0].pageX + touches[1].pageX) / 2,
            y: (touches[0].pageY + touches[1].pageY) / 2,
          };
        }
      },

      onPanResponderMove: (evt) => {
        const { touches } = evt.nativeEvent;
        if (touches.length === 1) {
          const dx = touches[0].pageX - lastPos.current.x;
          const dy = touches[0].pageY - lastPos.current.y;
          lastPos.current = { x: touches[0].pageX, y: touches[0].pageY };

          if (Math.abs(dx) > 0.1 || Math.abs(dy) > 0.1) {
            sendEvents(['m', Math.round(dx * 1.8), Math.round(dy * 1.8)]);
          }
        } else if (touches.length === 2) {
          // Two-finger scroll
          const curY = (touches[0].pageY + touches[1].pageY) / 2;
          const dy = curY - lastPos.current.y;
          lastPos.current.y = curY;

          if (Math.abs(dy) > 1) {
            sendEvents(['s', 0, dy > 0 ? -1 : 1]);
          }
        }
      },

      onPanResponderRelease: (evt) => {
        const elapsed = Date.now() - touchStartTime.current;
        const { touches } = evt.nativeEvent;

        // Detect quick tap (under 200ms without significant movement)
        if (elapsed < 200) {
          if (touches.length === 0) {
            // Tap -> Left Click
            sendEvents(['b', 1, 1], ['b', 1, 0]);
          } else if (touches.length === 1) {
            // 2-finger tap -> Right Click
            sendEvents(['b', 3, 1], ['b', 3, 0]);
          }
        }
      },
    })
  ).current;

  const handleSendText = () => {
    if (textInput.length > 0) {
      sendEvents(['type', textInput]);
      setTextInput('');
    }
  };

  const handleSendEnter = () => {
    sendEvents(['tap', 'Return']);
  };

  const handleSendBackspace = () => {
    sendEvents(['tap', 'BackSpace']);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />

      {/* Top Status Bar */}
      <View style={styles.topBar}>
        <TouchableOpacity
          style={styles.statusBadge}
          onPress={() => setModalVisible(true)}
        >
          <View
            style={[
              styles.statusDot,
              status === 'connected'
                ? styles.dotGreen
                : status === 'connecting'
                ? styles.dotYellow
                : styles.dotRed,
            ]}
          />
          <Text style={styles.statusText}>
            {status === 'connected' ? `Connected · ${rtt}ms` : status}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.settingsBtn}
          onPress={() => setModalVisible(true)}
        >
          <Text style={styles.settingsBtnText}>⚙ Config</Text>
        </TouchableOpacity>
      </View>

      {/* Main Trackpad Area */}
      <View style={styles.trackpad} {...panResponder.panHandlers}>
        <Text style={styles.trackpadHint}>
          Trackpad Area{'\n'}
          1-finger: Move & Tap{'\n'}
          2-finger: Scroll & Right-click
        </Text>
      </View>

      {/* Keyboard Input Strip */}
      <View style={styles.keyboardStrip}>
        <TextInput
          style={styles.input}
          placeholder="Type to remote machine..."
          placeholderTextColor="#64748b"
          value={textInput}
          onChangeText={setTextInput}
          onSubmitEditing={handleSendText}
          returnKeyType="send"
        />
        <TouchableOpacity style={styles.keyBtn} onPress={handleSendBackspace}>
          <Text style={styles.keyBtnText}>⌫</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.keyBtn} onPress={handleSendEnter}>
          <Text style={styles.keyBtnText}>⏎</Text>
        </TouchableOpacity>
      </View>

      {/* Mouse Buttons */}
      <View style={styles.buttonRow}>
        <TouchableOpacity
          style={[styles.clickBtn, styles.leftBtn]}
          onPress={() => sendEvents(['b', 1, 1], ['b', 1, 0])}
        >
          <Text style={styles.clickBtnText}>Left Click</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.clickBtn, styles.rightBtn]}
          onPress={() => sendEvents(['b', 3, 1], ['b', 3, 0])}
        >
          <Text style={styles.clickBtnText}>Right Click</Text>
        </TouchableOpacity>
      </View>

      {/* Connection Modal */}
      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>LANpad Server Config</Text>

            <Text style={styles.fieldLabel}>Host IP Address:</Text>
            <TextInput
              style={styles.modalInput}
              value={host}
              onChangeText={setHost}
              placeholder="e.g. 192.168.1.225"
              placeholderTextColor="#64748b"
              autoCapitalize="none"
            />

            <Text style={styles.fieldLabel}>Port:</Text>
            <TextInput
              style={styles.modalInput}
              value={port}
              onChangeText={setPort}
              placeholder="8765"
              placeholderTextColor="#64748b"
              keyboardType="numeric"
            />

            <Text style={styles.fieldLabel}>Auth Token:</Text>
            <TextInput
              style={styles.modalInput}
              value={token}
              onChangeText={setToken}
              placeholder="Token from lanpad console / URL hash"
              placeholderTextColor="#64748b"
              autoCapitalize="none"
            />

            <View style={styles.modalBtnRow}>
              <TouchableOpacity
                style={[styles.modalBtn, styles.btnCancel]}
                onPress={() => setModalVisible(false)}
              >
                <Text style={styles.modalBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalBtn, styles.btnConnect]}
                onPress={handleConnect}
              >
                <Text style={styles.modalBtnText}>Connect</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  dotGreen: { backgroundColor: '#10b981' },
  dotYellow: { backgroundColor: '#f59e0b' },
  dotRed: { backgroundColor: '#ef4444' },
  statusText: {
    color: '#e2e8f0',
    fontSize: 12,
    fontWeight: '600',
  },
  settingsBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#1e293b',
    borderRadius: 8,
  },
  settingsBtnText: {
    color: '#38bdf8',
    fontWeight: '600',
    fontSize: 13,
  },
  trackpad: {
    flex: 1,
    backgroundColor: 'rgba(30, 41, 59, 0.4)',
    margin: 12,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  trackpadHint: {
    color: '#475569',
    textAlign: 'center',
    lineHeight: 22,
    fontSize: 14,
  },
  keyboardStrip: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingBottom: 8,
    gap: 8,
  },
  input: {
    flex: 1,
    height: 44,
    backgroundColor: '#1e293b',
    borderRadius: 8,
    paddingHorizontal: 12,
    color: '#f8fafc',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  keyBtn: {
    width: 44,
    height: 44,
    backgroundColor: '#334155',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  keyBtnText: {
    color: '#f8fafc',
    fontSize: 18,
    fontWeight: '700',
  },
  buttonRow: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingBottom: 16,
    gap: 12,
  },
  clickBtn: {
    flex: 1,
    height: 52,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  leftBtn: {
    backgroundColor: '#0284c7',
  },
  rightBtn: {
    backgroundColor: '#334155',
  },
  clickBtnText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    width: '100%',
    backgroundColor: '#0f172a',
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 20,
    textAlign: 'center',
  },
  fieldLabel: {
    color: '#94a3b8',
    fontSize: 13,
    marginBottom: 6,
  },
  modalInput: {
    height: 44,
    backgroundColor: '#1e293b',
    borderRadius: 8,
    paddingHorizontal: 12,
    color: '#f8fafc',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    marginBottom: 16,
  },
  modalBtnRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  modalBtn: {
    flex: 1,
    height: 46,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnCancel: {
    backgroundColor: '#334155',
  },
  btnConnect: {
    backgroundColor: '#0284c7',
  },
  modalBtnText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});
