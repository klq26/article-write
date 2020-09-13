<template>
  <div id="app">
  <!-- 推荐热词 -->
  <h1 style='color:#FFF;font-size:0.6rem;' @click="changeRecommendWords()">词语推荐（点标题更换热词）</h1>
  <div class="recommend-words-panel">
    <div class="recommend-word" v-for="item in recommendWords" :key="item.index" @click="searchArticle(item.word)">
      {{item.word}}
    </div>
  </div>
  <!-- 搜索结果 -->
  <div class="result-panel">
    <div class="result" v-for="item in searchResults" :key="item.index">
      <!-- <div>{{item.article}}</div> -->
        <span style='color:#000'>{{item.article.substr(0, item.article.indexOf(selectedWord.toLowerCase()))}}</span>
        <span style='color:#FF0000'>{{item.article.substr(item.article.indexOf(selectedWord.toLowerCase()), selectedWord.length)}}</span>
        <span style='color:#000'>{{item.article.substr(item.article.toLowerCase().indexOf(selectedWord.toLowerCase())+selectedWord.length, item.article.length)}}</span>
      <br/>
      <a :href="item.url" target="_blank">原文地址：{{item.title}} 第 {{item.number}} 段</a>
    </div>
  </div>
  </div>
</template>

<script>
import HelloWorld from './components/HelloWorld'

import axios from 'axios'
import Vue from 'vue'

Vue.prototype.$axios = axios
Vue.config.productionTip = false

// 根据不同环境，动态切换 API 域名
var serverIp = process.env.API_ROOT

export default {
  name: 'App',
  components: {
    HelloWorld
  },
  data () {
    return {
      recommendWords: [],
      searchResults: [],
      selectedWord: ''
    }
  },
  methods: {
    getRandomKeywords () {
      var that = this
      axios.get(serverIp + 'article/api/recommend_words').then(function (response) {
        // 推荐词 20 个
        that.recommendWords = response.data.data
      })
    },
    changeRecommendWords () {
      this.getRandomKeywords()
    },
    searchArticle (word) {
      this.selectedWord = word
      this.getArticleByKeyword(word)
    },
    getArticleByKeyword (word) {
      var that = this
      axios.get(serverIp + 'article/api/keyword/' + word).then(function (response) {
        // 推荐词 20 个
        that.searchResults = response.data.data
      })
    }
  },
  created: function () {
    this.getRandomKeywords()
  }
}
</script>

<style>
#app {
  width: 10rem;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.recommend-words-panel {
  width: 10rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
}

.recommend-word {
  color: #000;
  background-color: #F0F0F0;
  width: 1.8rem;
  font-size: 0.4rem;
  margin: 4px;
  text-align: center;
}

.result-panel {
  width: 10rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
}

.result {
  color: #000;
  background-color: #F0F0F0;
  width: 10rem;
  font-size: 0.4rem;
  margin: 4px;
  text-align: left;
}

</style>
