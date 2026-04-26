
import { create } from 'zustand';

export const useStore = create((set) => ({
  isActivated: false,
  systemStatus: 'IDLE', // IDLE, SPEAKING, EXECUTING
  audioAmplitude: 0,
  activeProjects: [],
  sourceCode: [],
  hardware: [],
  neuralMap: { nodes: [], edges: [] },
  
  // Actions
  activateSystem: () => set({ isActivated: true }),
  setSystemStatus: (status) => set({ systemStatus: status }),
  setAudioAmplitude: (amplitude) => set({ audioAmplitude: amplitude }),
  updateFileSystem: (data) => set({ activeProjects: data.projects, sourceCode: data.source }),
  updateHardwareStatus: (data) => set({ hardware: data }),
  updateNeuralMap: (data) => set({ neuralMap: data }),
}));
