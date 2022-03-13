const kinds = ['punctual','cumulative'].map(u => document.getElementById(u));
var switchKind = function () {
    let id = this.value;
    kinds.forEach(u => u.style.display = 'none');
    document.getElementById(id).style.display = '';
}
