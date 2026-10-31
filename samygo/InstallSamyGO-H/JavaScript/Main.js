var Main = { }

var widgetAPI = new Common.API.Widget();
var tvKey = new Common.API.TVKeyValue();

var filePlugin;
var currentStep = 0;
var logMessage = "";

var timeoutValue = 5000;

var usbMountPath;
var data_zip = "data.zip";
var usbFound = false;
var widgetName="InstallSamyGO-H";
var skypePath = '/mtd_rwcommon/moip/engines/Skype';
var networkPath = '/mtd_rwarea/network';

Main.onLoad = function() {
	document.getElementById("anchor").focus();
	filePlugin = document.getElementById("pluginFileSystem");
	showTitle();
	widgetAPI.sendReadyEvent();
};

Main.onUnload = function(){ };

Main.keyDown = function() {
	var keyCode = event.keyCode;
	switch(keyCode) {
		case tvKey.KEY_RETURN:
		case tvKey.KEY_PANEL_RETURN:
			clearLog();
			widgetAPI.sendReturnEvent();
			break;
		case tvKey.KEY_UP:
		case tvKey.KEY_PANEL_UP:
			clearLog();
			break;
		case tvKey.KEY_ENTER:
		case tvKey.KEY_PANEL_ENTER:
			if (currentStep == 0) {
				clearLog();
				usbTest();
				setupSamyGO(usbMountPath);
			} else if (currentStep == 4) {
				rootSamyGO(usbMountPath);
			} else if (currentStep == 8)
			{
				logPara("<b style='color:green'>SamyGO activated!</b>");
			}
			else logPara("<b style='color:red'>SamyGO not activated! Check for errors!<b/>");
			break;
		default:
			break;
	} 
};

function runWidget(id)
{
    logPara("Running widget: <b style='color:green'>"+id+"</b>!");
    try
    {
        widgetAPI.runSearchWidget(id,"");
    }
    catch(e)
    {
        logPara("Exception: <b style='color:red'>"+e+"</b>!");
    }
}

function showTitle() {
	var titleDivElement = document.getElementById("title");
	var title = "Widget <b style='color:green'>" + curWidget.id + "</b> for Samsung SmartTV H-series";
	widgetAPI.putInnerHTML(titleDivElement, title);
	if (widgetName == curWidget.id) {
	/*
		if(exists("/mtd_rwcommon/emps/empBrowserCommonPlugin/plugins/libSamyGOrun.so"))
		{
			currentStep=-1;
			logPara("<b style='color:green'>SamyGO activated!!!</b>");
			logPara("<b style='color:green'>Widget will be closed automatically in " + Math.floor(timeoutValue/1000) + " seconds and " + (timeoutValue%1000) + " milliseconds!!!</b>");
			setTimeout("widgetAPI.sendExitEvent();",timeoutValue);
		}
		else
		{
		*/
			logPara("Press <b style='color:red'>Enter</b> or wait " + Math.floor(timeoutValue/1000) + " seconds and " + (timeoutValue%1000) + " milliseconds for activation " + curWidget.id + "!");
			setTimeout("if(currentStep == 0){clearLog();usbTest();setupSamyGO(usbMountPath);}",timeoutValue);
			
		//}
	} else {
		logPara("Current widget name '<b style='color:red'>" + curWidget.id + "</b>' differs from expected '"+widgetName+"'!");
	}
};

function log(message) {
	var logDivElement = document.getElementById("log");
	logMessage = logMessage + message + "<br>";
	widgetAPI.putInnerHTML(logDivElement, logMessage);
};

function logPara(message) {
	var logDivElement = document.getElementById("log");
	logMessage = logMessage + "<p>" + message + "</p>";
	widgetAPI.putInnerHTML(logDivElement, logMessage);
};

function clearLog() {
	var logDivElement = document.getElementById("log");
	logMessage = "";
	widgetAPI.putInnerHTML(logDivElement, logMessage);
};

function setupSamyGO(path) {
    logPara("*********************** Setup SamyGO files *************************************");
    var skypeNotFound = false;
    if(copy(networkPath + "/insmod_qca.sh",usbMountPath+"/"))
	{
        skypeNotFound = true;
		currentStep += 1;
	}
    else if(copy(networkPath + "/insmod_bcm.sh",usbMountPath+"/"))
	{
        skypeNotFound = true;
		data_zip="data_bcm.zip";
		currentStep += 1;
	}
    copy(networkPath + "/network_type_info",usbMountPath+"/network_type_info.txt");
    copy(networkPath + "/wifi_vendor",usbMountPath+"/wifi_vendor.txt");
    exists(networkPath + "/runSamyGO.sh");
    exists("/dtv/NET_OK");
    exists("/dtv/RUN_OK");
    exists("/mnt/rcSGO");
    exists(usbMountPath + "/SamyGO_OK.txt");
    exists(usbMountPath + "/SamyGO/vermagic.txt");
    currentStep += exists(usbMountPath + "/SamyGO/sfd.sh");
    currentStep += (exists(usbMountPath + "/SamyGO/samyext4.img") ||
                    exists(usbMountPath + "/SamyGO/newvdfs.img"));
    currentStep += exists(usbMountPath + "/" + widgetName + "/data/" + data_zip);

    if (currentStep == 4) {
        logPara("<span style='color:green'>All activation files found on: '"+ usbMountPath + "'</span>");
        logPara("Press <b style='color:red'>Enter</b> for activation " + curWidget.id + "!");
    } else {
        if (skypeNotFound) {
            logPara("<span style='color:red'>Network script not found.</span>");
        } else {
            logPara("<span style='color:red'>Some activation files not found on: '" + usbMountPath + "'</span>");
        }
        currentStep = -1;
    }
};

function rootSamyGO(path) {
    logPara("*********************** Root SamyGO files **************************************");

    currentStep += unzip(usbMountPath +"/" + widgetName + "/data/" + data_zip, networkPath + "/");
	if(data_zip == "data.zip")
    	currentStep += exists(networkPath + "/insmod_qca.sh");
	else
    	currentStep += exists(networkPath + "/insmod_bcm.sh");
    currentStep += exists(networkPath + "/busybox");
    currentStep += exists(networkPath + "/runSamyGO.sh");

    //if (currentStep == 7) {
    if (currentStep == 8) {
        logPara("<span style='color:green'>All activation files processed.</span>");
        logPara("<b style='color:green'>Now press exit and restart TV then test netcat on port 3023 or telnet on port 3123</b>");
    } else {
        logPara("<span style='color:red'>Some activation files not processed.</span>");
        logPara("<b style='color:red'>Read the rooting procedure.</b>");
        currentStep = -1;
    }
    log("Free memory: " + Math.round((filePlugin.GetTotalSize() - filePlugin.GetUsedSize())/1048576) + " Mbytes");
};

function usbTest() {
	logPara("*********************** USB test procedure *************************************");
	var usbPlugin = document.getElementById("pluginStorage");
	var nUSBCount = eval("usbPlugin.GetUSBListSize()");
	

	if (nUSBCount < 0) nUSBCount = 0;
	log("Found <b>" + nUSBCount + "</b> USB device(s)");
	for (var i = 0; i < nUSBCount; i++) {
		var nid = parseInt(eval("usbPlugin.GetUSBDeviceID(i)"));
		var nPartition = eval("usbPlugin.GetUSBPartitionNum(nid)");
		log("USB Device ID = " + nid + ", Vendor Model Name = " + eval("usbPlugin.GetUSBVendorName(nid)") + " " + eval("usbPlugin.GetUSBModelName(nid)") + ", no of partitions = " + nPartition);
		for (var j = 0; j < nPartition; j++) {
			usbMountPath = '/dtv/usb/' + eval("usbPlugin.GetUSBMountPath(nid, j)");
			log((j+1) + '. Mount path = <b>' + usbMountPath + '</b>'); // '$USB_DIR/'
			if(exists(usbMountPath + "/"+widgetName+"/data/data.zip"))
			{
				usbFound=true;
				break;
			}
		}
		if(usbFound)
			break;
	}
};

function status(result) {
	var color = (result == 1 ? "green" : "red");
	return "<span style='color:" + color +"'>" + (result == 1 ? "[OK]" : "[NO]") + "</span>";
};

function exists(from) {
	var command = "filePlugin.IsExistedPath('" + from + "')";
	var result = eval(command);
	log("Existing '" + from + "' ? " + status(result));
	return result == 1;
};

function unzip(from, to) {
	var command = "filePlugin.Unzip('" + from + "', '" + to + "')";
	var result = eval(command);
	log("Extracted '" + from + "' to '" + to +"' ? " + status(result));
	return result == 1;
};
function copy(from,to) {
    var command = "filePlugin.Copy('" + from + "','"+to+"')";
    var result = eval(command);
    log("Copying from:'" + from + "' to: '"+to+"'" + status(result));
    return result == 1;
};
