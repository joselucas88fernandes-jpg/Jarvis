
import { useEffect } from 'react';
import { useStore } from '@/lib/store';

export const useWebSocket = (url) => {
  const { 
    setSystemStatus, 
    setAudioAmplitude,
    updateFileSystem,
    updateHardwareStatus,
    updateNeuralMap
  } = useStore();

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('WebSocket Connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'system_status':
          setSystemStatus(data.payload.status); // e.g., 'SPEAKING', 'IDLE'
          break;
        case 'audio_amplitude':
          setAudioAmplitude(data.payload.amplitude);
          break;
        case 'file_system_update':
          updateFileSystem(data.payload);
          break;
        case 'hardware_update':
          updateHardwareStatus(data.payload);
          break;
        case 'neural_map_update':
          updateNeuralMap(data.payload);
          break;
        default:
          break;
      }
    };

    ws.onclose = () => {
      console.log('WebSocket Disconnected');
    };

    return () => {
      ws.close();
    };
  }, [url, setSystemStatus, setAudioAmplitude, updateFileSystem, updateHardwareStatus, updateNeuralMap]);
};
