import { useAuthStore } from "../store";

function hasPermission(allowedRoles) {
  if (!Array.isArray(allowedRoles) || allowedRoles.length === 0) return true;
  const authStore = useAuthStore();
  return authStore.hasRole(allowedRoles);
}

function removeElement(el) {
  if (!el.parentNode) return;
  if (!el.__permissionPlaceholder) {
    el.__permissionPlaceholder = document.createComment("v-permission");
  }
  el.parentNode.replaceChild(el.__permissionPlaceholder, el);
}

function restoreElement(el) {
  const placeholder = el.__permissionPlaceholder;
  if (!placeholder || !placeholder.parentNode || el.parentNode) return;
  placeholder.parentNode.replaceChild(el, placeholder);
}

export const permissionDirective = {
  mounted(el, binding) {
    if (!hasPermission(binding.value)) {
      removeElement(el);
    }
  },
  updated(el, binding) {
    if (!hasPermission(binding.value)) {
      removeElement(el);
      return;
    }
    restoreElement(el);
  }
};

