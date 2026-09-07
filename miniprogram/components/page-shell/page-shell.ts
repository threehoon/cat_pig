Component({
  options: {
    multipleSlots: true,
  },
  properties: {
    title: {
      type: String,
      value: '',
    },
    back: {
      type: Boolean,
      value: false,
    },
    catchBack: {
      type: Boolean,
      value: false,
    },
  },
  methods: {
    onNavBack() {
      this.triggerEvent('back')
    },
  },
})
