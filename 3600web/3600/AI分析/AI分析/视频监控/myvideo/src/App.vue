<script setup>

</script>
<template>
  <div class="app-view">
    <router-view></router-view>
  </div>
</template>
<style lang="less" >
body{
  background-color: #f3f4f8;
}
/* 清除所有元素默认内外边距，统一盒模型计算方式 */
* {
  margin: 0;
  padding: 0;
  /* 让width/height包含padding和border，避免计算偏差 */
  box-sizing: border-box;
}

/* 重置列表默认样式（去掉圆点/数字） */
ul, ol, li {
  list-style: none;
}

/* 重置链接默认样式（去掉下划线、统一颜色） */
a {
  text-decoration: none;
  color: inherit; /* 继承父元素颜色，避免默认蓝色 */
}

/* 重置图片默认行为（避免额外空隙、支持响应式） */
img {
  display: block; /* 解决inline图片底部空隙问题 */
  max-width: 100%; /* 图片不超过父容器宽度，响应式必备 */
  height: auto; /* 保持图片宽高比，防止拉伸变形 */
  border: none; /* 清除旧浏览器图片边框 */
}

/* 重置表单元素（统一样式、去除默认边框） */
input, button, select, textarea {
  outline: none; /* 清除聚焦时默认外边框 */
  border: none;
  background: transparent; /* 清除默认背景 */
  font-family: inherit; /* 继承全局字体，避免表单字体不一致 */
}

/* 清除button默认点击边框和禁用样式 */
button {
  cursor: pointer; /* 鼠标悬浮显示手型，提示可点击 */
  user-select: none; /* 禁止选中按钮文字 */
}
button:disabled {
  cursor: not-allowed; /* 禁用时显示禁止手型 */
  opacity: 0.6; /* 禁用时降低透明度，视觉区分 */
}
</style>
