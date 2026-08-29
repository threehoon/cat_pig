Component({
  properties: {
    image: { type: String, value: '' },
    title: { type: String, value: '' },
    hint: { type: String, value: '' },
    action: { type: String, value: '' },
  },
  methods: {
    onAction() {
      this.triggerEvent('action')
    },
  },
})
