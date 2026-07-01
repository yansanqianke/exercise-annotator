<!-- 全局布局：顶栏 + 侧边栏 + 主内容区 -->
<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const sidebarCollapsed = ref(false)

/** 侧边栏菜单 */
const menuItems = computed(() => {
  const items = [
    { group: '知识库', children: [
      { path: '/subjects', label: '学科管理', icon: '📚' },
      { path: '/knowledge-points', label: '知识点', icon: '🏷️' },
    ]},
    { group: '题目中心', children: [
      { path: '/annotate', label: '题目标注', icon: '✍️' },
      { path: '/documents', label: '文档解析', icon: '📄' },
    ]},
    { group: '工具', children: [
      { path: '/chat', label: 'AI 对话', icon: '💬' },
    ]},
  ]
  if (authStore.isAdmin) {
    items.push({ group: '系统管理', children: [
      { path: '/admin/users', label: '用户管理', icon: '👥' },
      { path: '/admin/llm-config', label: '大模型配置', icon: '⚙️' },
      { path: '/admin/agents', label: '智能体', icon: '🤖' },
      { path: '/admin/logs', label: '系统日志', icon: '📋' },
    ]})
  }
  return items
})

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function navigate(path) {
  router.push(path)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app-shell">
    <!-- 侧边栏 -->
    <aside :class="['sidebar', { collapsed: sidebarCollapsed }]">
      <div class="sidebar-brand" @click="router.push('/')">
        <span class="brand-icon">✦</span>
        <span v-show="!sidebarCollapsed" class="brand-text">习题标注</span>
      </div>

      <nav class="sidebar-nav">
        <template v-for="group in menuItems" :key="group.group">
          <div v-show="!sidebarCollapsed" class="nav-group-title">{{ group.group }}</div>
          <a
            v-for="item in group.children"
            :key="item.path"
            :class="['nav-item', { active: isActive(item.path) }]"
            @click="navigate(item.path)"
            :title="sidebarCollapsed ? item.label : ''"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span v-show="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
          </a>
        </template>
      </nav>

      <div class="sidebar-footer">
        <div class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? '▸' : '◂' }}
        </div>
      </div>
    </aside>

    <!-- 主区域 -->
    <div class="main-area">
      <!-- 顶栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <span class="topbar-title">{{ route.meta.title || '习题知识点标注智能体' }}</span>
        </div>
        <div class="topbar-right">
          <span class="user-badge">
            <span class="user-avatar">{{ authStore.user?.username?.charAt(0)?.toUpperCase() }}</span>
            {{ authStore.user?.username }}
          </span>
          <span class="role-tag">
            {{ authStore.isAdmin ? '管理员' : '教师' }}
          </span>
          <button class="btn-logout" @click="handleLogout">退出</button>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: var(--sidebar-width);
  background: #1e2433;
  color: #c8cdd8;
  display: flex;
  flex-direction: column;
  transition: width .25s cubic-bezier(.4,0,.2,1);
  flex-shrink: 0;
  overflow: hidden;
}
.sidebar.collapsed { width: var(--sidebar-collapsed); }

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 18px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,.08);
  user-select: none;
}
.brand-icon { font-size: 20px; color: var(--color-accent); flex-shrink: 0; }
.brand-text { font-family: var(--font-heading); font-size: 17px; font-weight: 600; color: #e8ecf2; white-space: nowrap; }

.sidebar-nav { flex: 1; overflow-y: auto; padding: 12px 0; }
.nav-group-title {
  padding: 12px 18px 6px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: rgba(255,255,255,.3);
  white-space: nowrap;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  cursor: pointer;
  color: rgba(255,255,255,.6);
  transition: all .15s;
  font-size: 14px;
  white-space: nowrap;
  border-left: 3px solid transparent;
}
.nav-item:hover { color: #fff; background: rgba(255,255,255,.06); }
.nav-item.active {
  color: #fff;
  background: rgba(255,255,255,.08);
  border-left-color: var(--color-accent);
}
.nav-icon { font-size: 16px; width: 24px; text-align: center; flex-shrink: 0; }
.nav-label { overflow: hidden; text-overflow: ellipsis; }

.sidebar-footer { padding: 12px 18px; border-top: 1px solid rgba(255,255,255,.08); }
.collapse-btn {
  cursor: pointer;
  color: rgba(255,255,255,.4);
  font-size: 14px;
  text-align: center;
  padding: 4px 0;
  transition: color .15s;
}
.collapse-btn:hover { color: #fff; }

/* ===== 主区域 ===== */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ===== 顶栏 ===== */
.topbar {
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-lg);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.topbar-title {
  font-family: var(--font-heading);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-badge { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--color-text-secondary); }
.user-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600;
}
.role-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--color-bg);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}
.btn-logout {
  background: none; border: none;
  color: var(--color-text-muted);
  font-size: 13px; cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: color .15s;
}
.btn-logout:hover { color: var(--color-danger); }

/* ===== 内容区 ===== */
.content {
  flex: 1;
  overflow-y: auto;
  background: var(--color-bg);
}
</style>
