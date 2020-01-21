function showHide() {
	var hiddeninputs = document.getElementsByClassName('hide');
	var commentbutton = document.getElementById("comment-button");

	if (commentbutton.innerHTML == "...show comments")
		commentbutton.innerHTML = "hide";
	else
		commentbutton.innerHTML = "...show comments"

	for(var i=0; i != hiddeninputs.length; i++){
		if (hiddeninputs[i].style.display == "block")
			hiddeninputs[i].style.display = "none";
		else
			hiddeninputs[i].style.display = "block";
	}
}