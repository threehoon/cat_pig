export function chooseLocalImages(count: number): Promise<string[]> {
  if (count <= 0) {
    return Promise.resolve([])
  }
  return new Promise((resolve, reject) => {
    wx.chooseMedia({
      count,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success(res) {
        resolve(res.tempFiles.map((file) => file.tempFilePath))
      },
      fail(err) {
        if (err.errMsg && err.errMsg.indexOf('cancel') !== -1) {
          resolve([])
          return
        }
        reject(err)
      },
    })
  })
}
