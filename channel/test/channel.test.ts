/**
 * ClawChats Channel Test Script
 * 
 * Tests:
 * 1. Connection
 * 2. Authentication
 * 3. Send message
 * 4. Receive message
 * 5. Reconnection
 */

import WebSocket from 'ws';

const TEST_CONFIG = {
  serverUrl: 'ws://localhost:8765/ws',
  userId: 'test-user-1',
  token: 'demo-token'
};

async function runTests() {
  console.log('🧪 ClawChats Channel Tests');
  console.log('=========================\n');
  
  let passed = 0;
  let failed = 0;
  
  // Test 1: Connection
  console.log('Test 1: Connection');
  try {
    const ws = new WebSocket(TEST_CONFIG.serverUrl);
    
    await new Promise((resolve, reject) => {
      ws.on('open', () => {
        console.log('✅ Connection successful\n');
        passed++;
        ws.close();
        resolve(true);
      });
      
      ws.on('error', (err) => {
        console.log('❌ Connection failed:', err.message, '\n');
        failed++;
        reject(err);
      });
      
      setTimeout(() => {
        console.log('❌ Connection timeout\n');
        failed++;
        ws.close();
        reject(new Error('Timeout'));
      }, 5000);
    });
  } catch (err) {
    failed++;
  }
  
  // Test 2: Authentication
  console.log('Test 2: Authentication');
  try {
    const ws = new WebSocket(TEST_CONFIG.serverUrl);
    
    await new Promise((resolve, reject) => {
      ws.on('open', () => {
        ws.send(JSON.stringify({
          type: 'auth',
          userId: TEST_CONFIG.userId,
          token: TEST_CONFIG.token
        }));
      });
      
      ws.on('message', (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.type === 'auth') {
          if (msg.ok) {
            console.log('✅ Authentication successful\n');
            passed++;
            ws.close();
            resolve(true);
          } else {
            console.log('❌ Authentication failed:', msg.error, '\n');
            failed++;
            ws.close();
            reject(new Error('Auth failed'));
          }
        }
      });
      
      ws.on('error', (err) => {
        console.log('❌ Auth error:', err.message, '\n');
        failed++;
        reject(err);
      });
      
      setTimeout(() => {
        console.log('❌ Auth timeout\n');
        failed++;
        ws.close();
        reject(new Error('Timeout'));
      }, 5000);
    });
  } catch (err) {
    failed++;
  }
  
  // Test 3: Send Message
  console.log('Test 3: Send Message');
  try {
    const ws = new WebSocket(TEST_CONFIG.serverUrl);
    let authenticated = false;
    
    await new Promise((resolve, reject) => {
      ws.on('open', () => {
        ws.send(JSON.stringify({
          type: 'auth',
          userId: TEST_CONFIG.userId,
          token: TEST_CONFIG.token
        }));
      });
      
      ws.on('message', (data) => {
        const msg = JSON.parse(data.toString());
        
        if (msg.type === 'auth' && msg.ok && !authenticated) {
          authenticated = true;
          console.log('  Authenticated, sending message...');
          
          ws.send(JSON.stringify({
            type: 'message',
            to: 'test-user-2',
            content: 'Hello from test!'
          }));
        }
        
        if (msg.type === 'ack' && authenticated) {
          console.log('✅ Message sent successfully\n');
          passed++;
          ws.close();
          resolve(true);
        }
      });
      
      ws.on('error', (err) => {
        console.log('❌ Send error:', err.message, '\n');
        failed++;
        reject(err);
      });
      
      setTimeout(() => {
        if (!authenticated) {
          console.log('❌ Send timeout (not authenticated)\n');
        } else {
          console.log('❌ Send timeout (no ack)\n');
        }
        failed++;
        ws.close();
        reject(new Error('Timeout'));
      }, 5000);
    });
  } catch (err) {
    failed++;
  }
  
  // Test 4: Receive Message
  console.log('Test 4: Receive Message');
  try {
    const ws1 = new WebSocket(TEST_CONFIG.serverUrl);
    const ws2 = new WebSocket(TEST_CONFIG.serverUrl);
    
    let ws1Ready = false;
    let ws2Ready = false;
    let messageReceived = false;
    
    await new Promise((resolve, reject) => {
      ws1.on('open', () => {
        ws1.send(JSON.stringify({
          type: 'auth',
          userId: 'test-receiver',
          token: TEST_CONFIG.token
        }));
      });
      
      ws1.on('message', (data) => {
        const msg = JSON.parse(data.toString());
        
        if (msg.type === 'auth' && msg.ok) {
          ws1Ready = true;
          console.log('  Receiver ready');
          
          if (ws2Ready) {
            sendMessage();
          }
        }
        
        if (msg.type === 'message' && msg.from === 'test-sender') {
          console.log('✅ Message received:', msg.content, '\n');
          passed++;
          messageReceived = true;
          ws1.close();
          ws2.close();
          resolve(true);
        }
      });
      
      ws2.on('open', () => {
        ws2.send(JSON.stringify({
          type: 'auth',
          userId: 'test-sender',
          token: TEST_CONFIG.token
        }));
      });
      
      ws2.on('message', (data) => {
        const msg = JSON.parse(data.toString());
        
        if (msg.type === 'auth' && msg.ok) {
          ws2Ready = true;
          console.log('  Sender ready');
          
          if (ws1Ready) {
            sendMessage();
          }
        }
      });
      
      function sendMessage() {
        console.log('  Sending test message...');
        ws2.send(JSON.stringify({
          type: 'message',
          to: 'test-receiver',
          content: 'Test message'
        }));
      }
      
      ws1.on('error', (err) => {
        console.log('❌ Receiver error:', err.message, '\n');
        failed++;
        reject(err);
      });
      
      ws2.on('error', (err) => {
        console.log('❌ Sender error:', err.message, '\n');
        failed++;
        reject(err);
      });
      
      setTimeout(() => {
        if (!messageReceived) {
          console.log('❌ Receive timeout\n');
          failed++;
        }
        ws1.close();
        ws2.close();
        reject(new Error('Timeout'));
      }, 5000);
    });
  } catch (err) {
    failed++;
  }
  
  // Test 5: Reconnection
  console.log('Test 5: Reconnection');
  try {
    const ws = new WebSocket(TEST_CONFIG.serverUrl);
    let connected = false;
    
    await new Promise((resolve, reject) => {
      ws.on('open', () => {
        if (!connected) {
          console.log('  Initial connection successful');
          connected = true;
          
          // Simulate disconnect
          setTimeout(() => {
            console.log('  Simulating disconnect...');
            ws.close();
            
            // Try to reconnect
            setTimeout(() => {
              const ws2 = new WebSocket(TEST_CONFIG.serverUrl);
              
              ws2.on('open', () => {
                console.log('✅ Reconnection successful\n');
                passed++;
                ws2.close();
                resolve(true);
              });
              
              ws2.on('error', (err) => {
                console.log('❌ Reconnection failed:', err.message, '\n');
                failed++;
                reject(err);
              });
            }, 1000);
          }, 1000);
        }
      });
      
      ws.on('error', (err) => {
        console.log('❌ Initial connection error:', err.message, '\n');
        failed++;
        reject(err);
      });
      
      setTimeout(() => {
        console.log('❌ Reconnection timeout\n');
        failed++;
        ws.close();
        reject(new Error('Timeout'));
      }, 10000);
    });
  } catch (err) {
    failed++;
  }
  
  // Summary
  console.log('=========================');
  console.log(`Results: ${passed} passed, ${failed} failed`);
  console.log('=========================\n');
  
  if (failed === 0) {
    console.log('🎉 All tests passed!');
    process.exit(0);
  } else {
    console.log('❌ Some tests failed');
    process.exit(1);
  }
}

// Run tests
runTests().catch(err => {
  console.error('Test runner error:', err);
  process.exit(1);
});
