// service-worker.js
const CACHE_NAME = 'safetyguard-cache-v1';
const urlsToCache = [
  '.',
  'index.html',
  'https://cdn.jsdelivr.net/npm/tailwindcss@3.3.0/dist/tailwind.min.css',
  'https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css',
  'https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.min.js'
];

// 安装Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
  // 立即激活，无需等待旧的Service Worker关闭
  self.skipWaiting();
});

// 缓存和返回请求
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // 如果找到缓存，返回缓存的响应
        if (response) {
          return response;
        }
        
        // 否则，发起网络请求
        return fetch(event.request)
          .then(response => {
            // 检查响应是否有效
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // 克隆响应，因为响应流只能使用一次
            const responseToCache = response.clone();
            
            // 将响应添加到缓存
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
            
            return response;
          })
          .catch(error => {
            // 网络请求失败，返回离线响应
            console.log('Network request failed, returning offline response', error);
            
            // 对于API请求，返回模拟数据
            if (event.request.url.includes('/api/')) {
              // 针对不同的API端点返回不同的模拟数据
              if (event.request.url.includes('/api/contacts')) {
                return new Response(JSON.stringify([
                  { id: 1, name: '张三', phone: '13800138001', relationship: '家人' },
                  { id: 2, name: '李四', phone: '13900139002', relationship: '朋友' },
                  { id: 3, name: '王五', phone: '13700137003', relationship: '同事' }
                ]), {
                  headers: { 'Content-Type': 'application/json' }
                });
              } else if (event.request.url.includes('/api/diaries')) {
                return new Response(JSON.stringify([
                  {
                    id: 1,
                    emotion: '开心',
                    content: '今天天气很好，心情愉快！',
                    created_at: new Date().toISOString()
                  },
                  {
                    id: 2,
                    emotion: '难过',
                    content: '今天遇到了一些困难，心情低落。',
                    created_at: new Date(Date.now() - 86400000).toISOString()
                  }
                ]), {
                  headers: { 'Content-Type': 'application/json' }
                });
              } else {
                return new Response(JSON.stringify({ error: 'Network unavailable' }), {
                  status: 503,
                  statusText: 'Service Unavailable',
                  headers: { 'Content-Type': 'application/json' }
                });
              }
            }
            
            // 对于其他请求，返回缓存的页面
            return caches.match('/index.html');
          });
      })
  );
});

// 更新Service Worker
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // 立即控制所有客户端
  self.clients.claim();
});

// 后台同步
self.addEventListener('sync', event => {
  if (event.tag === 'sync-data') {
    event.waitUntil(
      // 在这里执行后台同步操作，例如将本地存储的数据发送到服务器
      console.log('Background sync triggered')
    );
  }
});