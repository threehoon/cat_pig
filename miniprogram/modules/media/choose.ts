function pickImages(count: number, sourceType: Array<'album' | 'camera'>): Promise<string[]> {
  return new Promise((resolve, reject) => {
    wx.chooseMedia({
      count,
      mediaType: ['image'],
      sourceType,
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

export function chooseLocalImages(count: number): Promise<string[]> {
  if (count <= 0) {
    return Promise.resolve([])
  }
  return pickImages(count, ['album', 'camera']).catch(() => pickImages(count, ['album']))
}
