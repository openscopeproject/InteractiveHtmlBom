/* PCB AR code */
let pcbARStarted = false;
let arLocked = false;

function getARIframeContent() {
  return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AR View</title>
    <script src="https://aframe.io/releases/1.5.0/aframe.min.js"><\/script>
    <script src="https://cdn.jsdelivr.net/npm/mind-ar@1.2.5/dist/mindar-image-aframe.prod.js"><\/script>
    <style>
        body { margin: 0; padding: 0; overflow: hidden; }
    <\/style>
<\/head>
<body>
    <a-scene
        id="ar-scene"
        color-space="sRGB"
        renderer="colorManagement: true, physicallyCorrectLights"
        vr-mode-ui="enabled: false"
        device-orientation-permission-ui="enabled: false">

        <a-assets>
            <canvas id="pcb-canvas" width="512" height="512"><\/canvas>
        <\/a-assets>

        <a-camera position="0 0 0" look-controls="enabled: false" cursor="fuse: false; rayOrigin: mouse;" raycaster="far: 10000; objects: .clickable"><\/a-camera>

        <a-entity id="pcb-target" mindar-image-target="targetIndex: 0">
            <a-plane
                id="pcb-canvas-plane"
                class="clickable"
                material="src: #pcb-canvas; transparent: true; side: double"
                position="0 0 0"
                height="0.5625"
                width="1"
                rotation="0 0 0"
                opacity="0.8">
            <\/a-plane>
        <\/a-entity>
    <\/a-scene>

    <script>
        let arStarted = false;
        let arSystem = null;
        let opacityLevel = 0.8;
        let mindTargetSrc = null;
        let arInitialized = false;
        let arLocked = false;
        let lockedMatrix = null;
        let originalUpdateWorldMatrix = null;

        function initializeMindAR(targetSrc) {
            mindTargetSrc = targetSrc;
            const scene = document.getElementById('ar-scene');
            scene.setAttribute('mindar-image', {
                imageTargetSrc: targetSrc,
                autoStart: false
            });
            if (scene.hasLoaded) {
                setupARSystem();
            } else {
                scene.addEventListener('loaded', setupARSystem);
            }
        }

        function setupARSystem() {
            const scene = document.getElementById('ar-scene');
            arSystem = scene.systems['mindar-image-system'];
            arInitialized = true;
            if (window.parent !== window) {
                window.parent.postMessage({type: 'ar-ready'}, '*');
            }
        }

        function setupEventListeners() {
            const target = document.getElementById('pcb-target');
            if (target) {
                target.addEventListener('targetFound', function() {
                    if (window.parent !== window) {
                        window.parent.postMessage({type: 'pcb-detected'}, '*');
                    }
                });
                target.addEventListener('targetLost', function() {
                    if (window.parent !== window) {
                        window.parent.postMessage({type: 'pcb-lost'}, '*');
                    }
                });
            }
        }

        async function startAR() {
            try {
                if (!arInitialized || !arSystem) {
                    throw new Error('AR system not initialized');
                }
                await arSystem.start();
                arStarted = true;
                setupEventListeners();
                setupARClickDetection();
                if (window.parent !== window) {
                    window.parent.postMessage({type: 'ar-started'}, '*');
                }
            } catch (error) {
                if (window.parent !== window) {
                    window.parent.postMessage({type: 'ar-start-failed', error: error.message}, '*');
                }
            }
        }

        async function stopAR() {
            try {
                if (arSystem) {
                    await arSystem.stop();
                }
                arStarted = false;
                try {
                    const video = document.querySelector('video');
                    if (video && video.srcObject) {
                        const stream = video.srcObject;
                        const tracks = stream.getTracks();
                        tracks.forEach(track => track.stop());
                        video.srcObject = null;
                    }
                } catch (cleanupError) {}
                if (window.parent !== window) {
                    window.parent.postMessage({type: 'ar-stopped'}, '*');
                }
            } catch (error) {
                if (window.parent !== window) {
                    window.parent.postMessage({type: 'ar-stopped'}, '*');
                }
            }
        }

        function changeOpacity(value) {
            opacityLevel = parseFloat(value);
            const canvasPlane = document.getElementById('pcb-canvas-plane');
            if (canvasPlane) {
                canvasPlane.setAttribute('opacity', opacityLevel);
            }
        }

        function lockAR() {
            arLocked = true;
            const target = document.getElementById('pcb-target');

            if (target && target.components && target.components['mindar-image-target']) {
                const targetComponent = target.components['mindar-image-target'];

                if (target.object3D.visible && target.object3D.matrix) {
                    lockedMatrix = target.object3D.matrix.clone();

                    if (!originalUpdateWorldMatrix) {
                        originalUpdateWorldMatrix = targetComponent.updateWorldMatrix.bind(targetComponent);
                    }

                    targetComponent.updateWorldMatrix = function(worldMatrix) {
                        target.object3D.visible = true;
                        target.object3D.matrix = lockedMatrix;

                        target.emit("targetUpdate");
                    };
                }
            }
        }

        function unlockAR() {
            arLocked = false;
            const target = document.getElementById('pcb-target');

            if (target && target.components && target.components['mindar-image-target'] && originalUpdateWorldMatrix) {
                const targetComponent = target.components['mindar-image-target'];

                targetComponent.updateWorldMatrix = originalUpdateWorldMatrix;

                setTimeout(() => {
                    if (target.object3D.visible) {
                        // 如果目标可见，发送检测到的消息
                        if (window.parent !== window) {
                            window.parent.postMessage({type: 'pcb-detected'}, '*');
                        }
                    } else {
                        // 如果目标不可见，发送丢失的消息
                        if (window.parent !== window) {
                            window.parent.postMessage({type: 'pcb-lost'}, '*');
                        }
                    }
                }, 100);
            }

            lockedMatrix = null;
        }

        function setupARClickDetection() {
            const pcbPlane = document.getElementById('pcb-canvas-plane');
            if (pcbPlane) {
                pcbPlane.addEventListener('click', function(event) {
                    const intersection = event.detail.intersection;
                    if (intersection && intersection.uv) {
                        const uv = intersection.uv;
                        const clickData = {
                            uvX: uv.x,
                            uvY: 1 - uv.y,
                            worldPosition: intersection.point
                        };

                        if (window.parent !== window) {
                            window.parent.postMessage({
                                type: 'ar-pcb-click',
                                data: clickData
                            }, '*');
                        }
                    }
                });
            }
        }

        function updatePCBData(pcbData) {
            try {
                if (pcbData.imageData) {
                    const canvas = document.getElementById('pcb-canvas');
                    const ctx = canvas.getContext('2d');
                    const img = new Image();
                    img.onload = function() {
                        canvas.width = img.width;
                        canvas.height = img.height;
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(img, 0, 0);
                        const canvasPlane = document.getElementById('pcb-canvas-plane');
                        if (pcbData.pcbWidth && pcbData.pcbHeight) {
                            const aspectRatio = pcbData.pcbWidth / pcbData.pcbHeight;
                            const planeWidth = 1;
                            const planeHeight = 1 / aspectRatio;
                            canvasPlane.setAttribute('width', planeWidth);
                            canvasPlane.setAttribute('height', planeHeight);
                        }
                        const material = canvasPlane.getObject3D('mesh').material;
                        if (material && material.map) {
                            material.map.needsUpdate = true;
                        }
                        if (window.parent !== window) {
                            window.parent.postMessage({type: 'pcb-data-updated'}, '*');
                        }
                    };
                    img.src = pcbData.imageData;
                }
            } catch (error) {}
        }

        window.addEventListener('message', function(event) {
            if (event.data.type === 'init-ar-target') {
                initializeMindAR(event.data.targetSrc);
            } else if (event.data.type === 'start-ar') {
                startAR();
            } else if (event.data.type === 'stop-ar') {
                stopAR();
            } else if (event.data.type === 'update-pcb-data') {
                updatePCBData(event.data.data);
            } else if (event.data.type === 'change-opacity') {
                changeOpacity(event.data.value);
            } else if (event.data.type === 'lock-ar') {
                lockAR();
            } else if (event.data.type === 'unlock-ar') {
                unlockAR();
            }
        });

        document.addEventListener('DOMContentLoaded', function() {
            if (window.parent !== window) {
                window.parent.postMessage({type: 'ar-iframe-loaded'}, '*');
            }
        });
    <\/script>
<\/body>
<\/html>`;
}

function createARIframe() {
  const arcanvas = document.getElementById('arcanvas');
  if (!arcanvas) return;

  if (document.getElementById('ar-iframe')) {
    return;
  }

  const iframe = document.createElement('iframe');
  iframe.id = 'ar-iframe';
  iframe.srcdoc = getARIframeContent();
  iframe.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; background: transparent; pointer-events: auto;';
  iframe.setAttribute('allow', 'camera; microphone');

  arcanvas.insertBefore(iframe, arcanvas.firstChild);
}

function removeARIframe() {
  const arIframe = document.getElementById('ar-iframe');
  if (arIframe) {
    arIframe.remove();
  }
}

window.addEventListener('message', function(event) {
  const arIframe = document.getElementById('ar-iframe');
  if (!arIframe || event.source !== arIframe.contentWindow) return;

  switch(event.data.type) {
    case 'ar-iframe-loaded':
      const targetSrc = getCurrentARTargetFile();
      if (targetSrc) {
        arIframe.contentWindow.postMessage({
          type: 'init-ar-target',
          targetSrc: targetSrc
        }, '*');
      } else {
        document.getElementById('ar-status-text').textContent = 'Mind file not available';
        document.getElementById('ar-status-text').style.color = '#f44336';
      }
      break;
    case 'ar-ready':
      document.getElementById('ar-status-text').textContent = 'Searching';
      document.getElementById('ar-status-text').style.color = '#ff9800';

      setTimeout(function() {
        const arIframe = document.getElementById('ar-iframe');
        if (arIframe && arIframe.contentWindow) {
          arIframe.contentWindow.postMessage({
            type: 'change-opacity',
            value: settings.arOpacity / 100
          }, '*');
        }
      }, 500);
      break;
    case 'ar-started':
      pcbARStarted = true;
      document.getElementById('ar-status-text').textContent = 'Searching';
      document.getElementById('ar-status-text').style.color = '#ff9800';
      const startedDot = document.getElementById('ar-status-dot');
      if (startedDot) startedDot.style.background = '#ff9800';

      document.getElementById('ar-lock-btn').style.display = 'flex';

      function tryToSendPCBData(retryCount = 0) {
        const maxRetries = 10;
        const retryDelay = 200;

        if (retryCount >= maxRetries) {
          console.warn('Failed to send PCB data to AR after', maxRetries, 'retries');
          return;
        }

        var pcbData = getPCBCanvasData();
        if (pcbData) {
          sendPCBDataToAR();

          const arIframe = document.getElementById('ar-iframe');
          if (arIframe && arIframe.contentWindow) {
            arIframe.contentWindow.postMessage({
              type: 'change-opacity',
              value: settings.arOpacity / 100
            }, '*');
          }
        } else {
          setTimeout(() => tryToSendPCBData(retryCount + 1), retryDelay);
        }
      }

      setTimeout(tryToSendPCBData, 1000);
      break;
    case 'ar-stopped':
      pcbARStarted = false;
      arLocked = false;

      const arLockBtn = document.getElementById('ar-lock-btn');
      if (arLockBtn) {
        arLockBtn.style.display = 'none';
        arLockBtn.textContent = '🔓';
        arLockBtn.style.borderColor = 'rgba(255,255,255,0.3)';
        arLockBtn.style.background = 'rgba(255,255,255,0.1)';
      }

      window.arStoppedCallback && window.arStoppedCallback();
      break;
    case 'ar-start-failed':
      pcbARStarted = false;
      document.getElementById('ar-status-text').textContent = 'Failed';
      document.getElementById('ar-status-text').style.color = '#f44336';
      const failedDot = document.getElementById('ar-status-dot');
      if (failedDot) failedDot.style.background = '#f44336';
      break;
    case 'pcb-detected':
      if (!arLocked) {
        document.getElementById('ar-status-text').textContent = 'Locked';
        document.getElementById('ar-status-text').style.color = '#4CAF50';
        const detectedDot = document.getElementById('ar-status-dot');
        if (detectedDot) detectedDot.style.background = '#4CAF50';
      }
      break;
    case 'pcb-lost':
      if (!arLocked) {
        document.getElementById('ar-status-text').textContent = 'Searching';
        document.getElementById('ar-status-text').style.color = '#ff9800';
        const lostDot = document.getElementById('ar-status-dot');
        if (lostDot) lostDot.style.background = '#ff9800';
      }
      break;
    case 'ar-pcb-click':
      handleARPCBClick(event.data.data);
      break;
  }
});

function startPCBAR() {
  if (pcbARStarted) return;

  document.getElementById('ar-status-text').textContent = 'Searching';
  document.getElementById('ar-status-text').style.color = '#ff9800';

  const arIframe = document.getElementById('ar-iframe');
  if (arIframe && arIframe.contentWindow) {
    arIframe.contentWindow.postMessage({type: 'start-ar'}, '*');
  } else {
    document.getElementById('ar-status-text').textContent = 'Failed';
    document.getElementById('ar-status-text').style.color = '#f44336';
  }
}

function stopPCBAR(callback) {
  if (!pcbARStarted) {
    callback && callback();
    return;
  }

  if (callback) {
    window.arStoppedCallback = callback;
  }

  const arIframe = document.getElementById('ar-iframe');
  if (arIframe && arIframe.contentWindow) {
    arIframe.contentWindow.postMessage({type: 'stop-ar'}, '*');
  } else {
    callback && callback();
  }
}

function toggleARLock() {
  arLocked = !arLocked;
  const lockBtn = document.getElementById('ar-lock-btn');
  const statusText = document.getElementById('ar-status-text');
  const statusDot = document.getElementById('ar-status-dot');

  if (arLocked) {
    lockBtn.textContent = '🔒';
    lockBtn.title = 'Unlock AR position - Return to auto-tracking mode';
    lockBtn.style.borderColor = '#4CAF50';
    lockBtn.style.background = 'rgba(76, 175, 80, 0.2)';
    statusText.textContent = 'Locked (Manual)';
    statusText.style.color = '#4CAF50';
    if (statusDot) {
      statusDot.style.background = '#4CAF50';
    }

    const arIframe = document.getElementById('ar-iframe');
    if (arIframe && arIframe.contentWindow) {
      arIframe.contentWindow.postMessage({type: 'lock-ar'}, '*');
    }
  } else {
    lockBtn.textContent = '🔓';
    lockBtn.title = 'Lock AR position - Freeze overlay for stable viewing';
    lockBtn.style.borderColor = 'rgba(255,255,255,0.3)';
    lockBtn.style.background = 'rgba(255,255,255,0.1)';

    const arIframe = document.getElementById('ar-iframe');
    if (arIframe && arIframe.contentWindow) {
      arIframe.contentWindow.postMessage({type: 'unlock-ar'}, '*');
    }
  }
}

function handleARPCBClick(clickData) {
  var currentLayer = settings.canvaslayout;
  var layerdict = null;

  if (currentLayer === 'F') {
    layerdict = allcanvas.front;
  } else if (currentLayer === 'B') {
    layerdict = allcanvas.back;
  } else {
    layerdict = allcanvas.front;
  }

  if (!layerdict || !layerdict.bg) {
    console.warn('Layer data not available for AR click');
    return;
  }

  var canvasWidth = layerdict.bg.width;
  var canvasHeight = layerdict.bg.height;

  var flip = (layerdict.layer === "B");
  var bbox = applyRotation(pcbdata.edges_bbox, flip);
  var transform = layerdict.transform;

  var pcbWidth = (bbox.maxx - bbox.minx) * transform.s;
  var pcbHeight = (bbox.maxy - bbox.miny) * transform.s;
  var pcbX = transform.x + (bbox.minx * transform.s);
  var pcbY = transform.y + (bbox.miny * transform.s);

  if (flip) {
    pcbX = canvasWidth + transform.x - (bbox.maxx * transform.s);
  }

  var canvasClickX = pcbX + (clickData.uvX * pcbWidth);
  var canvasClickY = pcbY + (clickData.uvY * pcbHeight);

  var simulatedEvent = {
    offsetX: canvasClickX / devicePixelRatio,
    offsetY: canvasClickY / devicePixelRatio,
    hasOwnProperty: function(prop) { return prop === 'offsetX' || prop === 'offsetY'; }
  };

  handleMouseClick(simulatedEvent, layerdict);

  showARClickFeedback(canvasClickX, canvasClickY, layerdict);
}

function showARClickFeedback(x, y, layerdict) {
  var canvas = layerdict.highlight;
  var ctx = canvas.getContext('2d');

  ctx.save();

  ctx.strokeStyle = '#FF6B6B';
  ctx.fillStyle = 'rgba(255, 107, 107, 0.3)';
  ctx.lineWidth = 3;

  ctx.beginPath();
  ctx.arc(x, y, 20, 0, 2 * Math.PI);
  ctx.fill();
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(x - 15, y);
  ctx.lineTo(x + 15, y);
  ctx.moveTo(x, y - 15);
  ctx.lineTo(x, y + 15);
  ctx.stroke();

  ctx.restore();

  setTimeout(() => {
    redrawCanvas(layerdict);
  }, 1000);
}

function getPCBCanvasData() {
  try {
    var currentLayer = settings.canvaslayout;
    var layerdict = null;

    if (currentLayer === 'F') {
      layerdict = allcanvas.front;
    } else if (currentLayer === 'B') {
      layerdict = allcanvas.back;
    } else {
      layerdict = allcanvas.front;
    }

    if (!layerdict) {
      console.error('Failed to get layer data');
      return null;
    }

    if (!layerdict.bg || layerdict.bg.width === 0 || layerdict.bg.height === 0) {
      console.warn('Canvas not properly initialized, width:', layerdict.bg ? layerdict.bg.width : 'undefined', 'height:', layerdict.bg ? layerdict.bg.height : 'undefined');
      return null;
    }

    var flip = (layerdict.layer === "B");
    var bbox = applyRotation(pcbdata.edges_bbox, flip);
    var transform = layerdict.transform;

    var pcbWidth = (bbox.maxx - bbox.minx) * transform.s;
    var pcbHeight = (bbox.maxy - bbox.miny) * transform.s;

    var tempCanvas = document.createElement('canvas');
    var tempCtx = tempCanvas.getContext('2d');

    tempCanvas.width = Math.ceil(pcbWidth);
    tempCanvas.height = Math.ceil(pcbHeight);

    if (tempCanvas.width <= 0 || tempCanvas.height <= 0) {
      console.warn('Invalid temp canvas size:', tempCanvas.width, 'x', tempCanvas.height);
      return null;
    }

    var pcbX = transform.x + (bbox.minx * transform.s);
    var pcbY = transform.y + (bbox.miny * transform.s);

    if (flip) {
      pcbX = layerdict.bg.width + transform.x - (bbox.maxx * transform.s);
    }

    var sourceX = Math.max(0, Math.min(pcbX, layerdict.bg.width - pcbWidth));
    var sourceY = Math.max(0, Math.min(pcbY, layerdict.bg.height - pcbHeight));
    var sourceWidth = Math.min(pcbWidth, layerdict.bg.width - sourceX);
    var sourceHeight = Math.min(pcbHeight, layerdict.bg.height - sourceY);

    if (layerdict.bg && sourceWidth > 0 && sourceHeight > 0) {
      tempCtx.drawImage(layerdict.bg,
        sourceX, sourceY, sourceWidth, sourceHeight,
        0, 0, tempCanvas.width, tempCanvas.height
      );
    }

    if (settings.renderFabrication && layerdict.fab && sourceWidth > 0 && sourceHeight > 0) {
      tempCtx.drawImage(layerdict.fab,
        sourceX, sourceY, sourceWidth, sourceHeight,
        0, 0, tempCanvas.width, tempCanvas.height
      );
    }

    if (settings.renderSilkscreen && layerdict.silk && sourceWidth > 0 && sourceHeight > 0) {
      tempCtx.drawImage(layerdict.silk,
        sourceX, sourceY, sourceWidth, sourceHeight,
        0, 0, tempCanvas.width, tempCanvas.height
      );
    }

    if (layerdict.highlight && sourceWidth > 0 && sourceHeight > 0) {
      tempCtx.drawImage(layerdict.highlight,
        sourceX, sourceY, sourceWidth, sourceHeight,
        0, 0, tempCanvas.width, tempCanvas.height
      );
    }

    var imageData = tempCanvas.toDataURL('image/png');

    return {
      imageData: imageData,
      width: tempCanvas.width,
      height: tempCanvas.height,
      layer: currentLayer,
      transform: transform,
      bbox: bbox,
      pcbWidth: pcbWidth,
      pcbHeight: pcbHeight
    };

  } catch (error) {
    console.error('Failed to get PCB canvas data:', error);
    return null;
  }
}

function sendPCBDataToAR() {
  var pcbData = getPCBCanvasData();
  const arIframe = document.getElementById('ar-iframe');
  if (pcbData && arIframe && arIframe.contentWindow) {
    arIframe.contentWindow.postMessage({
      type: 'update-pcb-data',
      data: pcbData
    }, '*');
  } else if (!pcbData) {
    console.warn('PCB canvas data not ready, skipping AR update');
  }
}

function setARTargetFile(targetSrc) {
  const arIframe = document.getElementById('ar-iframe');
  if (arIframe && arIframe.contentWindow) {
    arIframe.contentWindow.postMessage({
      type: 'init-ar-target',
      targetSrc: targetSrc
    }, '*');
  }
}

async function initializeARMode() {
  document.getElementById("ar-btn").classList.add("depressed");

  document.getElementById("arcanvas").style.display = "block";

  const statusElement = document.getElementById('ar-status-text');
  if (statusElement) {
    statusElement.textContent = 'Checking environment...';
    statusElement.style.color = '#ff9800';
  }

  const cameraCheck = await checkCameraAvailability();

  if (!cameraCheck.available) {
    showCameraError(cameraCheck);

    document.getElementById("arcanvas").style.display = "none";

    document.getElementById("ar-btn").classList.remove("depressed");

    const previousLayout = settings.bomlayout === 'ar-view' ? 'left-right' : settings.bomlayout;
    changeBomLayout(previousLayout);
    return;
  }

  settings.bomlayout = 'ar-view';
  writeStorage("bomlayout", 'ar-view');
  setupARLayout();
}

function setupARLayout() {
  document.getElementById("frontcanvas").style.display = "";
  document.getElementById("backcanvas").style.display = "";
  document.getElementById("topmostdiv").style.height = "100%";
  document.getElementById("topmostdiv").style.display = "flex";
  document.getElementById("bot").style.height = "calc(100% - 80px)";
  document.getElementById("bomdiv").classList.add("split-horizontal");
  document.getElementById("canvasdiv").classList.add("split-horizontal");
  document.getElementById("frontcanvas").classList.remove("split-horizontal");
  document.getElementById("backcanvas").classList.remove("split-horizontal");

  if (bomsplit) {
    bomsplit.destroy();
    bomsplit = null;
  }
  if (canvassplit) {
    canvassplit.destroy();
    canvassplit = null;
  }

  bomsplit = Split(['#bomdiv', '#canvasdiv'], {
    sizes: [50, 50],
    onDragEnd: resizeAll,
    gutterSize: 5
  });
  canvassplit = Split(['#frontcanvas', '#backcanvas'], {
    sizes: [50, 50],
    gutterSize: 5,
    direction: "vertical",
    onDragEnd: resizeAll
  });

  document.getElementById("arcanvas").style.display = "block";
  createARIframe();

  document.getElementById("fl-btn").disabled = false;
  document.getElementById("fb-btn").disabled = true;
  document.getElementById("fb-btn").title = "FB mode not available in AR view";
  document.getElementById("bl-btn").disabled = false;

  document.getElementById("fl-btn").classList.remove("depressed");
  document.getElementById("fb-btn").classList.remove("depressed");
  document.getElementById("bl-btn").classList.remove("depressed");

  settings.canvaslayout = 'F';
  writeStorage("canvaslayout", 'F');
  document.getElementById("fl-btn").classList.add("depressed");

  setTimeout(function() {
    resizeAll();
    redrawIfInitDone();
  }, 200);

  setTimeout(function() {
    resizeAll();
    redrawIfInitDone();
  }, 500);

  setTimeout(function() {
    changeCanvasLayout('F');
  }, 600);

  setTimeout(function() {
    startPCBAR();
  }, 1000);
}

function updateARButtonStatus() {
  const envInfo = getEnvironmentInfo();
  const arButton = document.getElementById('ar-btn');

  if (arButton) {
    if (envInfo.supported) {
      arButton.title = `AR View (${envInfo.status})`;
      arButton.style.opacity = '1';
    } else {
      arButton.title = `AR View - ${envInfo.status} (Click for details)`;
      arButton.style.opacity = '0.7';
    }
  }
}

function getEnvironmentInfo() {
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const protocolCheck = checkProtocolSupport();

  let status = '';
  let statusColor = '';

  if (protocolCheck.supported) {
    if (protocol === 'https:') {
      status = 'Secure (HTTPS)';
      statusColor = '#4CAF50';
    } else {
      status = 'Secure (Localhost)';
      statusColor = '#4CAF50';
    }
  } else {
    if (protocol === 'file:') {
      status = 'File System (Insecure)';
      statusColor = '#f44336';
    } else {
      status = 'HTTP (Insecure)';
      statusColor = '#f44336';
    }
  }

  return {
    supported: protocolCheck.supported,
    status: status,
    color: statusColor,
    protocol: protocol,
    hostname: hostname
  };
}

function getCurrentFileName() {
  const path = window.location.pathname;
  const fileName = path.split('/').pop();
  return fileName || 'index.html';
}

function checkProtocolSupport() {
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const port = window.location.port;
  const currentURL = window.location.href;
  const fileName = getCurrentFileName();

  if (protocol === 'https:') {
    return { supported: true, error: null };
  }

  if (protocol === 'http:' && (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1')) {
    return { supported: true, error: null };
  }

  let errorMessage = 'Camera access requires a secure environment.\n\n';

  errorMessage += `Current environment:\n`;
  errorMessage += `• Protocol: ${protocol}\n`;
  errorMessage += `• Hostname: ${hostname || 'N/A'}\n`;
  if (port) {
    errorMessage += `• Port: ${port}\n`;
  }
  errorMessage += `• File: ${fileName}\n`;
  errorMessage += `• URL: ${currentURL}\n\n`;

  if (protocol === 'file:') {
    return {
      supported: false,
      error: null,
      isFileProtocol: true,
      fileName: fileName
    };
  } else if (protocol === 'http:') {
    errorMessage += 'Issue: HTTP is not secure enough for camera access.\n\n';
    errorMessage += 'Solutions:\n\n';
    errorMessage += '1. Use HTTPS instead of HTTP\n';
    errorMessage += '2. Or access via localhost:\n';
    errorMessage += `   • http://localhost/${fileName}\n`;
    errorMessage += `   • http://127.0.0.1/${fileName}`;
  } else {
    errorMessage += `Issue: Protocol "${protocol}" is not supported for camera access.\n\n`;
    errorMessage += 'Supported protocols:\n';
    errorMessage += '• https:// (recommended)\n';
    errorMessage += '• http://localhost/\n';
    errorMessage += '• http://127.0.0.1/';
  }

  return {
    supported: false,
    error: errorMessage
  };
}

async function checkCameraAvailability() {
  try {
    const protocolCheck = checkProtocolSupport();
    if (!protocolCheck.supported) {
      return {
        available: false,
        error: protocolCheck.error,
        isFileProtocol: protocolCheck.isFileProtocol,
        fileName: protocolCheck.fileName
      };
      }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return {
        available: false,
        error: 'Camera API not supported in this browser'
      };
    }

    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment'
      }
    });

    stream.getTracks().forEach(track => track.stop());

    return {
      available: true,
      error: null
    };

  } catch (error) {
    let errorMessage = 'Camera access failed';

    switch(error.name) {
      case 'NotAllowedError':
        errorMessage = 'Camera permission denied. Please allow camera access and try again.';
        break;
      case 'NotFoundError':
        errorMessage = 'No camera found on this device.';
        break;
      case 'NotReadableError':
        errorMessage = 'Camera is being used by another application.';
        break;
      case 'OverconstrainedError':
        errorMessage = 'Camera does not support the required settings.';
        break;
      case 'SecurityError':
        errorMessage = 'Camera access blocked due to security restrictions.';
        break;
      default:
        errorMessage = `Camera error: ${error.message}`;
        break;
    }

    return {
      available: false,
      error: errorMessage
    };
  }
}

function createCopyButton(elementId, title) {
  const copyButtonStyle = `
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: #444d56;
    border: 1px solid #586069;
    color: #e1e4e8;
    padding: 6px 8px;
    border-radius: 3px;
    font-size: 11px;
    cursor: pointer;
    height: 28px;
    width: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  `.replace(/\s+/g, ' ').trim();

  return `<button onclick="copyCommand('${elementId}', this)" style="${copyButtonStyle}" title="${title}">📋</button>`;
}

function showCameraError(errorData) {
  const errorDiv = document.createElement('div');
  errorDiv.id = 'camera-error-dialog';
  errorDiv.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border: 2px solid #f44336;
    border-radius: 8px;
    padding: 25px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    z-index: 10000;
    max-width: 600px;
    min-width: 400px;
    text-align: center;
    font-family: Arial, sans-serif;
    max-height: 80vh;
    overflow-y: auto;
  `;

  let contentHTML = '';

  if (typeof errorData === 'string') {
    errorData = { error: errorData };
  }

  if (errorData && errorData.isFileProtocol) {
    const fileName = errorData.fileName;
    contentHTML = `
      <div style="color: #f44336; font-size: 18px; font-weight: bold; margin-bottom: 15px;">
        Camera Not Available
      </div>
      <div style="color: #333; margin-bottom: 20px; line-height: 1.6; text-align: left;">
        <strong>Issue:</strong> You are opening this file directly from your file system.<br>
        Camera access requires a secure environment (HTTPS or localhost).
      </div>

      <div style="text-align: left; margin-bottom: 20px;">
        <div style="color: #333; font-weight: bold; margin-bottom: 10px;">💡 Quick Solution (Recommended):</div>
        <div style="background: #f6f8fa; border: 1px solid #d1d9e0; border-radius: 6px; padding: 16px; margin-bottom: 10px; position: relative;">
          <div style="color: #586069; font-size: 12px; margin-bottom: 8px;">1. Open terminal in this file's directory</div>
          <div style="background: #24292e; color: #e1e4e8; padding: 12px 50px 12px 12px; border-radius: 4px; font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; position: relative; min-height: 20px; display: flex; align-items: center;">
            <span id="python-command" style="flex: 1; line-height: 20px;">python -m http.server 8000</span>
            ${createCopyButton('python-command', 'Copy command')}
          </div>
          <div style="color: #586069; font-size: 12px; margin-top: 8px;">2. Then open this URL:</div>
          <div style="background: #24292e; color: #e1e4e8; padding: 12px 50px 12px 12px; border-radius: 4px; font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; position: relative; margin-top: 4px; min-height: 20px; display: flex; align-items: center;">
            <span id="url-command" style="flex: 1; line-height: 20px;">http://localhost:8000/${fileName}</span>
            ${createCopyButton('url-command', 'Copy URL')}
          </div>
        </div>
      </div>

      <details style="text-align: left; margin-bottom: 20px;">
        <summary style="cursor: pointer; color: #0366d6; font-weight: bold;">🔧 Other Options</summary>
        <div style="margin-top: 10px; padding-left: 20px;">
          <div style="margin-bottom: 15px;">
            <strong>Node.js:</strong><br>
            <code style="background: #f6f8fa; padding: 2px 4px; border-radius: 3px;">npm install -g http-server</code><br>
            <code style="background: #f6f8fa; padding: 2px 4px; border-radius: 3px;">http-server -p 8000</code>
          </div>
          <div style="margin-bottom: 15px;">
            <strong>PHP:</strong><br>
            <code style="background: #f6f8fa; padding: 2px 4px; border-radius: 3px;">php -S localhost:8000</code>
          </div>
          <div style="margin-bottom: 15px;">
            <strong>VS Code:</strong><br>
            Install "Live Server" extension → Right-click file → "Open with Live Server"
          </div>
        </div>
      </details>
    `;
  } else {
    const errorMessage = typeof errorData === 'string' ? errorData : (errorData.error || 'Unknown error');
    contentHTML = `
      <div style="color: #f44336; font-size: 18px; font-weight: bold; margin-bottom: 10px;">
        Camera Not Available
      </div>
      <div style="color: #333; margin-bottom: 15px; line-height: 1.6; text-align: left; white-space: pre-line;">
        ${errorMessage}
      </div>
    `;
  }

  contentHTML += `
    <div style="text-align: center; margin-top: 20px;">
      <button onclick="closeCameraError()" style="
        background: #f44336;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
      ">OK</button>
    </div>
  `;

  errorDiv.innerHTML = contentHTML;

  const overlay = document.createElement('div');
  overlay.id = 'camera-error-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    z-index: 9999;
  `;

  document.body.appendChild(overlay);
  document.body.appendChild(errorDiv);
}

function copyToClipboard(text, buttonElement, originalColor = '#e1e4e8') {
  if (!buttonElement) return;

  const originalText = buttonElement.textContent;
  const originalBackground = buttonElement.style.background;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      buttonElement.textContent = '✓';
      buttonElement.style.background = '#28a745';
      buttonElement.style.color = '#fff';

      setTimeout(() => {
        buttonElement.textContent = originalText;
        buttonElement.style.background = originalBackground;
        buttonElement.style.color = originalColor;
      }, 2000);
    }).catch(() => {
      buttonElement.textContent = '✗';
      buttonElement.style.background = '#dc3545';
      buttonElement.style.color = '#fff';

      setTimeout(() => {
        buttonElement.textContent = originalText;
        buttonElement.style.background = originalBackground;
        buttonElement.style.color = originalColor;
      }, 2000);
    });
  } else {
    buttonElement.textContent = '✗';
    buttonElement.style.background = '#dc3545';
    buttonElement.style.color = '#fff';

    setTimeout(() => {
      buttonElement.textContent = originalText;
      buttonElement.style.background = originalBackground;
      buttonElement.style.color = originalColor;
    }, 2000);
  }
}

function copyCommand(elementId, buttonElement) {
  const element = document.getElementById(elementId);
  if (!element) return;

  const text = element.textContent;
  copyToClipboard(text, buttonElement, '#e1e4e8');
}

function copyServerCommand(buttonElement) {
  const fileName = getCurrentFileName();
  const command = `python -m http.server 8000`;
  const url = `http://localhost:8000/${fileName}`;
  const fullCommand = `${command}\n\nThen open: ${url}`;

  copyToClipboard(fullCommand, buttonElement, '');
}

function closeCameraError() {
  const errorDiv = document.getElementById('camera-error-dialog');
  const overlay = document.getElementById('camera-error-overlay');

  if (errorDiv) errorDiv.remove();
  if (overlay) overlay.remove();
}

function getCurrentARTargetFile() {
  if (settings.bomlayout === "ar-view" && pcbdata && pcbdata.ar_config && pcbdata.ar_config.enabled) {
    switch(settings.canvaslayout) {
      case 'F':
        if (pcbdata.ar_config.front_mind_data) {
          return 'data:application/octet-stream;base64,' + pcbdata.ar_config.front_mind_data;
        }
        break;
      case 'B':
        if (pcbdata.ar_config.back_mind_data) {
          return 'data:application/octet-stream;base64,' + pcbdata.ar_config.back_mind_data;
        }
        break;
      default:
        if (pcbdata.ar_config.front_mind_data) {
          return 'data:application/octet-stream;base64,' + pcbdata.ar_config.front_mind_data;
        }
        break;
    }
  }

  console.error('AR mind file data not available');
  return null;
}

function completeARReload() {
  const layerName = settings.canvaslayout === 'F' ? 'Front' : 'Back';

  document.getElementById('ar-status-text').textContent = `Switching to ${layerName}`;
  document.getElementById('ar-status-text').style.color = '#ff9800';

  const wasARRunning = pcbARStarted;

  exitARMode(function() {
    document.getElementById('ar-status-text').textContent = `Loading ${layerName} AR`;
    document.getElementById('ar-status-text').style.color = '#ff9800';

    setTimeout(function() {
      enterARMode(wasARRunning);
    }, 300);
  });
}

function exitARMode(callback) {
  if (pcbARStarted) {
    stopPCBAR(function() {
      removeARIframe();
      document.getElementById("arcanvas").style.display = "none";

      callback && callback();
    });
  } else {
    removeARIframe();
    document.getElementById("arcanvas").style.display = "none";

    callback && callback();
  }
}

function enterARMode(shouldStartAR) {
  document.getElementById("arcanvas").style.display = "block";

  createARIframe();

  document.getElementById("fl-btn").disabled = false;
  document.getElementById("fb-btn").disabled = true;
  document.getElementById("fb-btn").title = "FB mode not available in AR view";
  document.getElementById("bl-btn").disabled = false;

  document.getElementById("fl-btn").classList.remove("depressed");
  document.getElementById("bl-btn").classList.remove("depressed");

  if (settings.canvaslayout === 'F') {
    document.getElementById("fl-btn").classList.add("depressed");
  } else if (settings.canvaslayout === 'B') {
    document.getElementById("bl-btn").classList.add("depressed");
  }

  if (shouldStartAR) {
    setTimeout(function() {
      startPCBAR();
    }, 1000);
  } else {
    setTimeout(function() {
      document.getElementById('ar-status-text').textContent = 'Ready';
      document.getElementById('ar-status-text').style.color = '#666';
    }, 1500);
  }
}