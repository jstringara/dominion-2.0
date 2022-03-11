const inputs = document.getElementsByTagName('input');
const button = document.getElementById('button');

function toggleButton() {
    if (button.value < 2) {
        button.disabled = true;
    } else {
        button.disabled = false;
    }
}
var fun = function updateTourNum() {
    this.previousElementSibling.value = 1-this.previousElementSibling.value;
    let checked = [...inputs].map(input => Number(input.checked));
    let num = checked.reduce((acc, cur) => acc + cur, 0);
    button.value = num;
    toggleButton();
}
//uso jquery per sottomettere tutto il form
$('form').submit(function(){

    $(":checkbox:not(:checked)").each(function(element, index){
        $(this).attr({value: '0', checked:'checked'});
    });

    return true;
});
