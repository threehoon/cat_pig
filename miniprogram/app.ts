import { login } from './core/auth'

App<IAppOption>({
  globalData: {},
  onLaunch() {
    login().catch(() => undefined)
  },
})
