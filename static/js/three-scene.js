import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

(function () {
    'use strict';

    const BUILDING_SPECS = {
        gate: { width: 54, depth: 12, height: 14 },
        teaching: { width: 62, depth: 30, height: 42 },
        library: { width: 56, depth: 42, height: 34 },
        canteen: { width: 66, depth: 40, height: 24 },
        dorm: { width: 74, depth: 28, height: 52 },
        gym: { width: 58, depth: 58, height: 28 },
        office: { width: 44, depth: 34, height: 40 },
        modern: { width: 54, depth: 38, height: 46 }
    };

    function latLngToWorld(loc, center) {
        const latScale = 111320;
        const lngScale = 111320 * Math.cos(center.lat * Math.PI / 180);
        return new THREE.Vector3(
            (loc.lng - center.lng) * lngScale,
            0,
            (loc.lat - center.lat) * latScale
        );
    }

    function colorToHex(hex) {
        return new THREE.Color(hex || '#4285f4');
    }

    function makeWindowMaterial(color) {
        return new THREE.MeshStandardMaterial({
            color: 0xffffff,
            emissive: color,
            emissiveIntensity: 0.28,
            roughness: 0.35
        });
    }

    function addWindows(parent, width, height, depth, color, facade) {
        const winColor = new THREE.Color(0x9bd7ff);
        const winMat = makeWindowMaterial(winColor);
        const rows = Math.max(2, Math.floor(height / 7));
        const gapY = height / rows;
        let cols;
        if (facade === 'x') cols = Math.max(3, Math.floor(width / 11));
        else cols = Math.max(3, Math.floor(depth / 11));
        const gapX = (facade === 'x' ? width : depth) / cols;
        const winW = Math.min(2.2, gapX * 0.42);
        const winH = Math.min(2.6, gapY * 0.42);
        const axisOffset = facade === 'x' ? depth / 2 + 0.15 : width / 2 + 0.15;

        for (let side of [-1, 1]) {
            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    const win = new THREE.Mesh(new THREE.BoxGeometry(
                        facade === 'x' ? winW : winH,
                        winH,
                        facade === 'x' ? winH : winW
                    ), winMat);
                    const along = -((facade === 'x' ? width : depth) / 2) + gapX / 2 + c * gapX;
                    const y = -height / 2 + gapY / 2 + r * gapY;
                    if (facade === 'x') {
                        win.position.set(along, y, side * axisOffset);
                    } else {
                        win.position.set(side * axisOffset, y, along);
                    }
                    parent.add(win);
                }
            }
        }
    }

    function createBaseBuilding(loc, color) {
        const spec = BUILDING_SPECS[loc.type] || BUILDING_SPECS.modern;
        const group = new THREE.Group();
        const material = new THREE.MeshStandardMaterial({
            color: colorToHex(loc.color || color),
            roughness: 0.62,
            metalness: 0.08
        });
        const body = new THREE.Mesh(
            new THREE.BoxGeometry(spec.width, spec.height, spec.depth),
            material
        );
        body.position.y = spec.height / 2;
        body.castShadow = true;
        body.receiveShadow = true;
        body.name = 'body';
        group.add(body);

        const roofMat = new THREE.MeshStandardMaterial({ color: 0x455a64, roughness: 0.75 });
        const roof = new THREE.Mesh(
            new THREE.BoxGeometry(spec.width * 0.82, 1.8, spec.depth * 0.82),
            roofMat
        );
        roof.position.y = spec.height + 0.9;
        roof.castShadow = true;
        roof.receiveShadow = true;
        roof.name = 'roof';
        group.add(roof);

        addWindows(group, spec.width, spec.height, spec.depth, color, 'x');
        addWindows(group, spec.width, spec.height, spec.depth, color, 'z');
        group.userData = {
            id: loc.id,
            name: loc.name,
            desc: loc.desc || '',
            open: loc.open || '全天开放',
            type: loc.type,
            width: spec.width,
            depth: spec.depth,
            height: spec.height
        };
        return group;
    }

    function createSpecialBuilding(loc, color) {
        const group = new THREE.Group();
        const baseColor = colorToHex(loc.color || color);
        const mat = new THREE.MeshStandardMaterial({ color: baseColor, roughness: 0.58 });
        const darkMat = new THREE.MeshStandardMaterial({ color: 0x37474f, roughness: 0.7 });

        if (loc.type === 'gate') {
            const pillarMat = new THREE.MeshStandardMaterial({ color: 0x8d6e63, roughness: 0.7 });
            const top = new THREE.Mesh(new THREE.BoxGeometry(54, 5, 12), pillarMat);
            top.position.y = 12;
            top.castShadow = true;
            group.add(top);
            [-20, 20].forEach(x => {
                const pillar = new THREE.Mesh(new THREE.CylinderGeometry(2.8, 3.4, 13, 12), pillarMat);
                pillar.position.set(x, 6.5, 0);
                pillar.castShadow = true;
                group.add(pillar);
            });
            const nameBoard = new THREE.Mesh(new THREE.BoxGeometry(34, 3.2, 1.2),
                new THREE.MeshStandardMaterial({ color: 0xfff8e1, roughness: 0.4 }));
            nameBoard.position.set(0, 8, 6.3);
            group.add(nameBoard);
            group.userData = {
                id: loc.id, name: loc.name, desc: loc.desc || '', open: loc.open || '',
                type: loc.type, width: 54, depth: 12, height: 14
            };
            return group;
        }

        if (loc.type === 'gym') {
            const base = new THREE.Mesh(new THREE.CylinderGeometry(34, 38, 12, 48), mat);
            base.position.y = 6;
            base.castShadow = true;
            base.receiveShadow = true;
            group.add(base);
            const dome = new THREE.Mesh(new THREE.SphereGeometry(32, 36, 20, 0, Math.PI * 2, 0, Math.PI / 2), darkMat);
            dome.position.y = 12;
            dome.castShadow = true;
            group.add(dome);
            const ring = new THREE.Mesh(new THREE.TorusGeometry(30, 1.1, 10, 64), mat);
            ring.rotation.x = Math.PI / 2;
            ring.position.y = 12.2;
            group.add(ring);
            group.userData = {
                id: loc.id, name: loc.name, desc: loc.desc || '', open: loc.open || '',
                type: loc.type, width: 58, depth: 58, height: 28
            };
            return group;
        }

        if (loc.type === 'dorm') {
            const towerCount = 3;
            const towerWidth = 18;
            const towerDepth = 18;
            const towerHeight = 52;
            const gap = 27;
            const startX = -((towerCount - 1) * gap) / 2;
            for (let i = 0; i < towerCount; i++) {
                const towerGroup = new THREE.Group();
                towerGroup.position.set(startX + i * gap, 0, 0);
                const tower = new THREE.Mesh(
                    new THREE.BoxGeometry(towerWidth, towerHeight, towerDepth),
                    mat
                );
                tower.position.set(0, towerHeight / 2, 0);
                tower.castShadow = true;
                tower.receiveShadow = true;
                towerGroup.add(tower);
                addWindows(towerGroup, towerWidth, towerHeight, towerDepth, baseColor, 'x');
                addWindows(towerGroup, towerWidth, towerHeight, towerDepth, baseColor, 'z');
                group.add(towerGroup);
            }
            const base = new THREE.Mesh(new THREE.BoxGeometry(86, 5, 26), darkMat);
            base.position.y = 2.5;
            base.castShadow = true;
            group.add(base);
            group.userData = {
                id: loc.id, name: loc.name, desc: loc.desc || '', open: loc.open || '',
                type: loc.type, width: 74, depth: 28, height: 52
            };
            return group;
        }

        if (loc.type === 'library') {
            const podium = new THREE.Mesh(new THREE.BoxGeometry(70, 6, 54), darkMat);
            podium.position.y = 3;
            podium.castShadow = true;
            podium.receiveShadow = true;
            group.add(podium);
            const main = new THREE.Mesh(new THREE.BoxGeometry(46, 26, 34), mat);
            main.position.y = 19;
            main.castShadow = true;
            main.receiveShadow = true;
            group.add(main);
            const steps = new THREE.Mesh(new THREE.CylinderGeometry(22, 26, 7, 6), darkMat);
            steps.position.set(0, 3, 25);
            steps.castShadow = true;
            group.add(steps);
            addWindows(group, 46, 26, 34, baseColor, 'x');
            addWindows(group, 46, 26, 34, baseColor, 'z');
            group.userData = {
                id: loc.id, name: loc.name, desc: loc.desc || '', open: loc.open || '',
                type: loc.type, width: 56, depth: 42, height: 34
            };
            return group;
        }

        if (loc.type === 'modern') {
            const base = new THREE.Mesh(new THREE.BoxGeometry(52, 28, 38), mat);
            base.position.y = 14;
            base.castShadow = true;
            base.receiveShadow = true;
            group.add(base);
            const top = new THREE.Mesh(new THREE.BoxGeometry(38, 20, 28), darkMat);
            top.position.y = 38;
            top.rotation.y = Math.PI / 4;
            top.castShadow = true;
            group.add(top);
            const core = new THREE.Mesh(new THREE.CylinderGeometry(6, 8, 60, 20), new THREE.MeshStandardMaterial({ color: 0xcfd8dc, roughness: 0.4 }));
            core.position.set(18, 30, -12);
            core.castShadow = true;
            group.add(core);
            addWindows(group, 52, 28, 38, baseColor, 'x');
            addWindows(group, 52, 28, 38, baseColor, 'z');
            group.userData = {
                id: loc.id, name: loc.name, desc: loc.desc || '', open: loc.open || '',
                type: loc.type, width: 54, depth: 38, height: 46
            };
            return group;
        }

        return createBaseBuilding(loc, color);
    }

    function createRoadSegment(a, b) {
        const dx = b.x - a.x;
        const dz = b.z - a.z;
        const length = Math.sqrt(dx * dx + dz * dz);
        if (length < 0.01) return null;
        const group = new THREE.Group();
        const road = new THREE.Mesh(
            new THREE.BoxGeometry(length + 4, 0.35, 8),
            new THREE.MeshStandardMaterial({ color: 0x616a75, roughness: 0.9 })
        );
        road.position.set((a.x + b.x) / 2, 0.12, (a.z + b.z) / 2);
        road.rotation.y = -Math.atan2(dz, dx);
        road.receiveShadow = true;
        group.add(road);

        const midLine = new THREE.Mesh(
            new THREE.BoxGeometry(length - 2, 0.42, 0.5),
            new THREE.MeshStandardMaterial({ color: 0xffd54f, roughness: 0.7 })
        );
        midLine.position.copy(road.position);
        midLine.position.y = 0.3;
        midLine.rotation.y = road.rotation.y;
        group.add(midLine);
        return group;
    }

    function createTree(x, z, scale) {
        const group = new THREE.Group();
        const trunkMat = new THREE.MeshStandardMaterial({ color: 0x795548, roughness: 0.9 });
        const leafMat = new THREE.MeshStandardMaterial({ color: 0x2e7d32, roughness: 0.8 });
        const h = 4.5 * scale;
        const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.5 * scale, 0.7 * scale, h, 8), trunkMat);
        trunk.position.y = h / 2;
        trunk.castShadow = true;
        group.add(trunk);
        const canopy = new THREE.Mesh(new THREE.ConeGeometry(2.6 * scale, 5.2 * scale, 8), leafMat);
        canopy.position.y = h + 2.2 * scale;
        canopy.castShadow = true;
        group.add(canopy);
        group.position.set(x, 0, z);
        return group;
    }

    function createFountain(center) {
        const group = new THREE.Group();
        const stone = new THREE.Mesh(new THREE.CylinderGeometry(16, 18, 2, 48),
            new THREE.MeshStandardMaterial({ color: 0xb0bec5, roughness: 0.7 }));
        stone.position.y = 1;
        stone.receiveShadow = true;
        group.add(stone);
        const water = new THREE.Mesh(new THREE.CylinderGeometry(13, 13, 1.4, 48),
            new THREE.MeshStandardMaterial({ color: 0x29b6f6, roughness: 0.2, metalness: 0.15 }));
        water.position.y = 1.7;
        group.add(water);
        const jet = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 2.4, 10, 12),
            new THREE.MeshStandardMaterial({ color: 0x81d4fa, roughness: 0.25, transparent: true, opacity: 0.75 }));
        jet.position.y = 7;
        group.add(jet);
        group.position.copy(center);
        group.position.y = 0;
        return group;
    }

    async function initCampus3D(options) {
        const container = document.getElementById(options.containerId || 'campus3d-container');
        const loadingEl = document.getElementById(options.loadingId || 'campus3d-loading');
        const errorEl = document.getElementById(options.errorId || 'campus3d-error');
        const toolbarEl = document.getElementById(options.toolbarId || 'campus3d-toolbar');
        const infoEl = document.getElementById(options.infoId || 'campus3d-info');
        const searchPanelEl = document.getElementById(options.searchId || 'campus3d-search-panel');
        const searchInputEl = document.getElementById(options.searchInputId || 'campus3d-search-input');
        const searchListEl = document.getElementById(options.searchListId || 'campus3d-search-list');

        function showError(message) {
            if (loadingEl) loadingEl.style.display = 'none';
            if (errorEl) {
                errorEl.style.display = 'flex';
                errorEl.innerHTML =
                    '<div class="campus3d-error-card"><div class="campus3d-error-icon">⚠️</div>' +
                    '<h2>3D 场景加载失败</h2><p>' + message + '</p>' +
                    '<button type="button" onclick="location.reload()">重新加载</button>' +
                    '<a href="/dashboard">返回主面板</a></div>';
            }
        }

        let campusData;
        try {
            const res = await fetch('/api/campus');
            campusData = await res.json();
            if (!res.ok || !campusData || !campusData.success || !campusData.locations) {
                throw new Error((campusData && campusData.message) || '校园数据接口异常');
            }
        } catch (err) {
            showError('无法获取校园地点数据，请确认后端服务已启动。');
            throw err;
        }

        const locations = campusData.locations;
        const roadsData = campusData.roads || [];
        const tourOrder = campusData.tour_order || locations.map(l => l.id);
        const center = {
            lat: locations.reduce((s, l) => s + l.lat, 0) / locations.length,
            lng: locations.reduce((s, l) => s + l.lng, 0) / locations.length
        };

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x87ceeb);
        scene.fog = new THREE.Fog(0x87ceeb, 550, 1800);

        const camera = new THREE.PerspectiveCamera(48, container.clientWidth / container.clientHeight, 0.1, 4000);
        const initialCameraPos = new THREE.Vector3(520, 330, 520);
        camera.position.set(900, 560, 900);

        const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        container.appendChild(renderer.domElement);

        const labelRenderer = new CSS2DRenderer();
        labelRenderer.setSize(container.clientWidth, container.clientHeight);
        labelRenderer.domElement.style.position = 'absolute';
        labelRenderer.domElement.style.top = '0';
        labelRenderer.domElement.style.left = '0';
        labelRenderer.domElement.style.pointerEvents = 'none';
        container.appendChild(labelRenderer.domElement);

        const controls = new OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 0, 0);
        controls.enableDamping = true;
        controls.dampingFactor = 0.08;
        controls.minDistance = 60;
        controls.maxDistance = 1700;
        controls.maxPolarAngle = Math.PI / 2.05;
        controls.screenSpacePanning = true;
        controls.update();

        const hemiLight = new THREE.HemisphereLight(0xffffff, 0x9bc995, 0.95);
        scene.add(hemiLight);
        const sunLight = new THREE.DirectionalLight(0xffffff, 1.9);
        sunLight.position.set(360, 520, 260);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 2048;
        sunLight.shadow.mapSize.height = 2048;
        sunLight.shadow.camera.left = -900;
        sunLight.shadow.camera.right = 900;
        sunLight.shadow.camera.top = 900;
        sunLight.shadow.camera.bottom = -900;
        sunLight.shadow.camera.near = 10;
        sunLight.shadow.camera.far = 1800;
        sunLight.shadow.bias = -0.0004;
        scene.add(sunLight);

        const ground = new THREE.Mesh(
            new THREE.PlaneGeometry(2800, 2800),
            new THREE.MeshStandardMaterial({ color: 0x7cb342, roughness: 0.95 })
        );
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.2;
        ground.receiveShadow = true;
        scene.add(ground);

        const grid = new THREE.GridHelper(2000, 40, 0xcfe8b8, 0xcfe8b8);
        grid.position.y = 0.02;
        scene.add(grid);

        const roadGroup = new THREE.Group();
        roadGroup.name = 'roads';
        const locWorld = new Map();
        locations.forEach(loc => locWorld.set(loc.id, latLngToWorld(loc, center)));

        roadsData.forEach(pair => {
            const a = locWorld.get(pair[0]);
            const b = locWorld.get(pair[1]);
            if (!a || !b) return;
            const road = createRoadSegment(a, b);
            if (road) roadGroup.add(road);
        });
        scene.add(roadGroup);

        const buildingGroup = new THREE.Group();
        buildingGroup.name = 'buildings';
        const labelGroup = new THREE.Group();
        labelGroup.name = 'labels';
        const interactiveMeshes = [];
        const buildingGroups = [];

        locations.forEach(loc => {
            const pos = locWorld.get(loc.id);
            if (!pos) return;
            const building = createSpecialBuilding(loc, loc.color);
            building.position.set(pos.x, 0, pos.z);
            building.traverse(child => {
                if (child.isMesh) {
                    child.castShadow = child.castShadow !== false;
                    child.receiveShadow = child.receiveShadow !== false;
                    interactiveMeshes.push(child);
                }
            });
            buildingGroup.add(building);
            buildingGroups.push(building);

            const labelDiv = document.createElement('div');
            labelDiv.className = 'campus3d-label';
            labelDiv.textContent = loc.name;
            const label = new CSS2DObject(labelDiv);
            label.position.set(pos.x, (building.userData.height || 20) + 7, pos.z);
            labelGroup.add(label);
        });
        scene.add(buildingGroup);
        scene.add(labelGroup);

        // 绿化：避开建筑和道路随机放置
        let treeSeed = 42;
        function pseudoRandom() {
            treeSeed = (treeSeed * 16807) % 2147483647;
            return (treeSeed - 1) / 2147483646;
        }
        for (let i = 0; i < 180; i++) {
            const angle = pseudoRandom() * Math.PI * 2;
            const radius = 120 + pseudoRandom() * 760;
            const x = Math.cos(angle) * radius;
            const z = Math.sin(angle) * radius;
            let tooClose = false;
            for (const loc of locations) {
                const p = locWorld.get(loc.id);
                if (p && Math.hypot(p.x - x, p.z - z) < 55) {
                    tooClose = true;
                    break;
                }
            }
            if (!tooClose) {
                const tree = createTree(x, z, 0.7 + pseudoRandom() * 0.8);
                scene.add(tree);
            }
        }

        const fountain = createFountain(new THREE.Vector3(0, 0, 0));
        scene.add(fountain);

        const raycaster = new THREE.Raycaster();
        const pointer = new THREE.Vector2();
        let selectedBuilding = null;
        let flyTarget = null;
        let introStart = performance.now();
        let tourActive = false;
        let tourIndex = 0;
        let tourTimer = null;
        let nightMode = false;
        let labelsVisible = true;
        let roadsVisible = true;

        function showInfo(building) {
            if (!infoEl) return;
            infoEl.style.display = 'block';
            infoEl.querySelector('.campus3d-info-name').textContent = building.userData.name;
            infoEl.querySelector('.campus3d-info-desc').textContent = building.userData.desc || '暂无介绍';
            infoEl.querySelector('.campus3d-info-open').textContent = '开放时间：' + (building.userData.open || '全天开放');
            const goBtn = infoEl.querySelector('[data-action="go"]');
            if (goBtn) {
                goBtn.onclick = () => focusBuilding(building);
            }
        }

        function setHighlight(building, on) {
            building.traverse(child => {
                if (!child.isMesh || !child.material) return;
                if (Array.isArray(child.material)) {
                    child.material.forEach(m => {
                        m.emissive = m.emissive || new THREE.Color(0x000000);
                        m.emissiveIntensity = on ? 0.45 : 0;
                    });
                } else {
                    child.material.emissive = child.material.emissive || new THREE.Color(0x000000);
                    child.material.emissiveIntensity = on ? 0.45 : 0;
                }
            });
        }

        function focusBuilding(building, keepTour) {
            const pos = new THREE.Vector3();
            building.getWorldPosition(pos);
            flyTarget = pos.clone();
            if (selectedBuilding && selectedBuilding !== building) {
                setHighlight(selectedBuilding, false);
            }
            selectedBuilding = building;
            setHighlight(building, true);
            showInfo(building);
            if (tourActive && !keepTour) stopTour();
        }

        function resetView() {
            if (selectedBuilding) setHighlight(selectedBuilding, false);
            selectedBuilding = null;
            if (infoEl) infoEl.style.display = 'none';
            flyTarget = new THREE.Vector3(0, 0, 0);
            if (tourActive) stopTour();
        }

        function onPointerMove(event) {
            const rect = renderer.domElement.getBoundingClientRect();
            pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            raycaster.setFromCamera(pointer, camera);
            const hits = raycaster.intersectObjects(interactiveMeshes, false);
            renderer.domElement.style.cursor = hits.length ? 'pointer' : 'grab';
        }

        function onPointerClick(event) {
            const rect = renderer.domElement.getBoundingClientRect();
            pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            raycaster.setFromCamera(pointer, camera);
            const hits = raycaster.intersectObjects(interactiveMeshes, false);
            if (!hits.length) {
                resetView();
                return;
            }
            let obj = hits[0].object;
            let building = null;
            while (obj && !building) {
                if (obj.userData && obj.userData.id && obj.parent) {
                    building = buildingGroups.find(g => g.userData.id === obj.userData.id);
                }
                obj = obj.parent;
            }
            if (building) focusBuilding(building);
        }

        function renderSearchList(filter) {
            if (!searchListEl) return;
            searchListEl.innerHTML = '';
            const keyword = (filter || '').trim().toLowerCase();
            const filtered = locations.filter(l =>
                !keyword || l.name.toLowerCase().includes(keyword) || l.type.toLowerCase().includes(keyword)
            );
            filtered.forEach(loc => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'campus3d-search-item';
                btn.innerHTML = '<span class="campus3d-search-dot" style="background:' + loc.color + '"></span>' +
                    '<span>' + loc.name + '</span><small>' + loc.desc + '</small>';
                btn.addEventListener('click', () => {
                    const building = buildingGroups.find(g => g.userData.id === loc.id);
                    if (building) focusBuilding(building);
                    if (searchPanelEl) searchPanelEl.classList.remove('is-open');
                });
                searchListEl.appendChild(btn);
            });
        }

        function bindButtons() {
            const byId = id => document.getElementById(id);
            byId('campus3d-reset')?.addEventListener('click', resetView);
            byId('campus3d-route')?.addEventListener('click', () => {
                roadsVisible = !roadsVisible;
                roadGroup.visible = roadsVisible;
                byId('campus3d-route').classList.toggle('is-active', roadsVisible);
            });
            byId('campus3d-labels')?.addEventListener('click', () => {
                labelsVisible = !labelsVisible;
                labelGroup.visible = labelsVisible;
                byId('campus3d-labels').classList.toggle('is-active', labelsVisible);
            });
            byId('campus3d-night')?.addEventListener('click', () => {
                nightMode = !nightMode;
                byId('campus3d-night').classList.toggle('is-active', nightMode);
                scene.background = new THREE.Color(nightMode ? 0x0b1c3d : 0x87ceeb);
                scene.fog.color = new THREE.Color(nightMode ? 0x0b1c3d : 0x87ceeb);
                hemiLight.intensity = nightMode ? 0.25 : 0.95;
                sunLight.intensity = nightMode ? 0.55 : 1.9;
            });
            byId('campus3d-tour')?.addEventListener('click', () => {
                if (tourActive) stopTour();
                else startTour();
            });
            byId('campus3d-search-open')?.addEventListener('click', () => {
                searchPanelEl?.classList.toggle('is-open');
                if (searchPanelEl?.classList.contains('is-open')) searchInputEl?.focus();
            });
            byId('campus3d-search-close')?.addEventListener('click', () => {
                searchPanelEl?.classList.remove('is-open');
            });
            searchInputEl?.addEventListener('input', e => renderSearchList(e.target.value));
            byId('campus3d-info-close')?.addEventListener('click', () => {
                resetView();
            });
            renderSearchList('');
        }

        function startTour() {
            if (!tourOrder.length) return;
            tourActive = true;
            tourIndex = 0;
            const tourBtn = document.getElementById('campus3d-tour');
            if (tourBtn) tourBtn.textContent = '⏸️ 暂停漫游';
            focusLocationInOrder();
            tourTimer = window.setInterval(focusLocationInOrder, 3800);
        }

        function stopTour() {
            tourActive = false;
            if (tourTimer) window.clearInterval(tourTimer);
            tourTimer = null;
            const tourBtn = document.getElementById('campus3d-tour');
            if (tourBtn) tourBtn.textContent = '🎥 自动漫游';
        }

        function focusLocationInOrder() {
            const id = tourOrder[tourIndex % tourOrder.length];
            const building = buildingGroups.find(g => g.userData.id === id);
            if (building) focusBuilding(building, true);
            tourIndex = (tourIndex + 1) % tourOrder.length;
        }

        const keys = {};
        function onKeyDown(e) {
            keys[e.key.toLowerCase()] = true;
            if (e.key === 'Escape') {
                if (searchPanelEl?.classList.contains('is-open')) searchPanelEl.classList.remove('is-open');
                else resetView();
            }
        }
        function onKeyUp(e) {
            keys[e.key.toLowerCase()] = false;
        }

        function handleMovement(delta) {
            const speed = 110 * delta;
            const forward = new THREE.Vector3();
            camera.getWorldDirection(forward);
            forward.y = 0;
            forward.normalize();
            const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();
            const move = new THREE.Vector3();
            if (keys['w'] || keys['arrowup']) move.add(forward);
            if (keys['s'] || keys['arrowdown']) move.sub(forward);
            if (keys['a'] || keys['arrowleft']) move.sub(right);
            if (keys['d'] || keys['arrowright']) move.add(right);
            if (move.lengthSq() > 0) {
                move.normalize().multiplyScalar(speed);
                controls.target.add(move);
                controls.target.x = THREE.MathUtils.clamp(controls.target.x, -1100, 1100);
                controls.target.z = THREE.MathUtils.clamp(controls.target.z, -1100, 1100);
            }
        }

        function animate() {
            requestAnimationFrame(animate);
            const now = performance.now();
            const delta = Math.min(0.05, (now - window._campusLastTime || now) / 1000);
            window._campusLastTime = now;

            // 开场从高空平滑进入
            const introElapsed = (now - introStart) / 1000;
            if (introElapsed < 2.4) {
                const t = Math.min(1, introElapsed / 2.4);
                const ease = 1 - Math.pow(1 - t, 3);
                camera.position.lerpVectors(new THREE.Vector3(900, 560, 900), initialCameraPos, ease);
            }

            if (flyTarget) {
                controls.target.lerp(flyTarget, 0.07);
                if (controls.target.distanceTo(flyTarget) < 0.4) flyTarget = null;
            }

            handleMovement(delta);
            controls.update();
            renderer.render(scene, camera);
            labelRenderer.render(scene, camera);
        }

        renderer.domElement.addEventListener('pointermove', onPointerMove);
        renderer.domElement.addEventListener('click', onPointerClick);
        window.addEventListener('resize', () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
            labelRenderer.setSize(container.clientWidth, container.clientHeight);
        });
        window.addEventListener('keydown', onKeyDown);
        window.addEventListener('keyup', onKeyUp);

        bindButtons();
        if (loadingEl) loadingEl.style.display = 'none';
        if (toolbarEl) toolbarEl.classList.add('is-visible');
        if (searchPanelEl) searchPanelEl.classList.remove('is-open');
        animate();

        return {
            scene,
            camera,
            controls,
            focusBuilding,
            resetView,
            stopTour
        };
    }

    window.Campus3D = { init: initCampus3D };
})();
