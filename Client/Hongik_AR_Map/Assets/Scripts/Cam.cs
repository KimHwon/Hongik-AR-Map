using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using System;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;

public class Cam : MonoBehaviour
{
    WebCamTexture webCamTexture = null;
    Socket image_sock = null;
    Socket data_sock = null;

    enum DataFormat : byte
    {
        EMPTY   = 0x00,
        TEXT    = 0x01,
        SENSOR  = 0x02,
        DEST    = 0x03
    };
    const byte ETX = 0x03;

    byte[] buffer = new byte[1024];

    bool onGPS = false;
    
    // Start is called before the first frame update
    void Start()
    {
        webCamTexture = new WebCamTexture();
        GetComponent<Renderer>().material.mainTexture = webCamTexture; //Add Mesh Renderer to the GameObject to which this script is attached to
        webCamTexture.Play();

        data_sock = Loading.Instance.GetDatatSocket();
        image_sock = Loading.Instance.GetImageSocket();

        StartCoroutine("TakePhoto");


        // Require GPS permission.
        UnityEngine.Android.Permission.RequestUserPermission("android.permission.ACCESS_FINE_LOCATION");
        
        Input.location.Start(5f, 5f);
    }

    // Update is called once per frame
    void Update()
    {
        for (int i = 0; i < buffer.Length; i++) buffer[i] = (byte)DataFormat.EMPTY;

        if (Input.touchCount > 0)
        {
            FormatMessage("save");
        }
        else if (Input.GetKeyDown(KeyCode.Escape))
        {
            Application.Quit();
        }
        else if (onGPS)
        {
            float[] datas = new float[12];
            for (int x = 0; x < datas.Length; x++) datas[x] = 0f;

            datas[0] = Input.location.lastData.latitude;
            datas[1] = Input.location.lastData.longitude;
            datas[2] = Input.location.lastData.altitude;

            FormatSensor(datas);

            SetText("DebugText", "Location: " + datas[0].ToString() + ", " + datas[1].ToString());
        }
        else
        {
            
        }
        
        data_sock.Send(buffer, 1024, SocketFlags.None); // Client must send first.

        data_sock.Receive(buffer, 1024, SocketFlags.None);
        // do something with `buffer`.


        if (!Input.location.isEnabledByUser)
        {
            SetText("DebugText", "Disabled");
        }
        else if (Input.location.status == LocationServiceStatus.Initializing)
        {
            SetText("DebugText", "Init");
        }
        else if (Input.location.status == LocationServiceStatus.Failed)
        {
            SetText("DebugText", "Failed");
        }
        else
        {
            onGPS = true;
        }

    }

    void OnApplicationQuit()
    {
        if (image_sock != null) image_sock.Close();
        if (data_sock != null)
        {
            for (int i = 0; i < buffer.Length; i++) buffer[i] = (byte)DataFormat.EMPTY;
            FormatMessage("save");

            data_sock.Send(buffer, 1024, SocketFlags.None);
            data_sock.Close();
        }


    }

    IEnumerator TakePhoto()
    {
        while (true) {
            yield return new WaitForSeconds(.5f);
            // NOTE - you almost certainly have to do this here:
            yield return new WaitForEndOfFrame(); 

            // it's a rare case where the Unity doco is pretty clear,
            // http://docs.unity3d.com/ScriptReference/WaitForEndOfFrame.html
            // be sure to scroll down to the SECOND long example on that doco page 

            Texture2D photo = new Texture2D(webCamTexture.width, webCamTexture.height);
            photo.SetPixels(webCamTexture.GetPixels());
            photo.Apply();

            try
            {
                //Encode to a JPG
                byte[] bytes = photo.EncodeToJPG();

                //SetText("DebugText", bytes.Length.ToString());

                image_sock.Send(bytes, SocketFlags.None);
            }
            catch (Exception e)
            {
                SetText("DebugText", e.ToString());
            }
        }
    }

    void FormatMessage(string str)
    {
        int i;
        byte[] msg = Encoding.UTF8.GetBytes(str);
        buffer[0] = (byte)DataFormat.TEXT;
        for (i = 0; i < Math.Min(buffer.Length-2, msg.Length); i++)
            buffer[i+1] = msg[i];
        buffer[i+1] = ETX;
    }
    void FormatSensor(float[] datas)
    {
        if (datas.Length != 12) return;

        buffer[0] = (byte)DataFormat.SENSOR;
        int i = 1;
        for (int j = 0; j < 12; j++)
        {
            byte[] bytes = BitConverter.GetBytes(datas[j]);
            for (int k = 0; k < bytes.Length; k++)
            {
                buffer[i] = bytes[k];
                i++;
            }
        }
    }

    void SetText(string name, string str) {
        GameObject debugText = GameObject.Find(name);
        if (debugText != null) {
            TextMesh textMesh = debugText.GetComponent("TextMesh") as TextMesh;
            if (textMesh != null) {
                textMesh.text = str;
            }
        }
    }
}