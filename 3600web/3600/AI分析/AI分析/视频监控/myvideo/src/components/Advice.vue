<script setup>
const props = defineProps({
  name:{
    type: String,
  },
  advices:{
    type: Array,
  }
})

</script>

<template>
  <div class="advice-box" style="width: 21.7vw">
    <h5 style="font-size: 0.8vw">{{name}}</h5>
    <ul>
      <li style="font-size: 0.5vw" v-for="(item,index) in advices">({{index+1}}).{{item}}</li>
    </ul>
  </div>
</template>

<style scoped>
.advice-box{
  padding: 0.5vw;
  //margin-left: 0.5vw;
  background-color: #f3f4f8;
  border-radius: 0.2vw;
  margin-bottom: 1vh;

}
li{
  //margin-left: 0.5vw;
}
</style>
