
'use client';

import { useWebSocket } from '@/hooks/useWebSocket';
import ActivationPortal from '@/components/hud/ActivationPortal';
import CentralCore from '@/components/hud/CentralCore';
import DirectoryDisplay from '@/components/hud/DirectoryDisplay';
import HardwareStatus from '@/components/hud/HardwareStatus';
import NeuralMap from '@/components/hud/NeuralMap';
import { useStore } from '@/lib/store';

const WEBSOCKET_URL = 'ws://<IP_OF_NODE_1>:8765'; // Your Python WebSocket server

export default function Home() {
  useWebSocket(WEBSOCKET_URL);
  const { isActivated } = useStore();

  return (
    <main className="relative w-screen h-screen overflow-hidden">
      <ActivationPortal />
      
      {isActivated && (
        <div className="w-full h-full p-8 grid grid-cols-4 grid-rows-3 gap-8">
          <div className="col-span-1 row-span-3">
            <DirectoryDisplay />
          </div>
          <div className="col-span-3 row-span-1">
            <HardwareStatus />
          </div>
          <div className="col-span-3 row-span-2">
            <NeuralMap />
          </div>
        </div>
      )}
      
      <CentralCore />
    </main>
  );
}
