/* 轻量 toast 单例：跨组件共享一条短暂提示。 */

import { readonly, ref, type Ref } from 'vue'

const visible = ref(false)
const message = ref('')
let timer: ReturnType<typeof setTimeout> | null = null

export interface ToastApi {
  visible: Readonly<Ref<boolean>>
  message: Readonly<Ref<string>>
  show(text: string): void
}

const api: ToastApi = {
  visible: readonly(visible),
  message: readonly(message),
  show(text: string): void {
    message.value = text
    visible.value = true
    if (timer !== null) clearTimeout(timer)
    timer = setTimeout(() => {
      visible.value = false
      timer = null
    }, 2200)
  },
}

export function useToast(): ToastApi {
  return api
}
