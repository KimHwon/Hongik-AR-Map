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

    Socket image_sock = Loading.Instance.GetImageSocket();
    Socket data_sock = Loading.Instance.GetDatatSocket();
    string IP = Loading.Instance.GetIP();

    enum DataFormat : byte
    {
        EMPTY   = 0x00,
        TEXT    = 0x01,
        SENSOR  = 0x02,
        DEST    = 0x03
    };
    const byte ETX = 0x03;

    byte[] buffer = new byte[1024];

    Boolean isInputCompleted = false;
    
    // Start is called before the first frame update
    void Start()
    {
        webCamTexture = new WebCamTexture();
        GetComponent<Renderer>().material.mainTexture = webCamTexture; //Add Mesh Renderer to the GameObject to which this script is attached to
        webCamTexture.Play();

        StartCoroutine("TakePhoto");
    }

    // Update is called once per frame
    void Update()
    {
        for (int i = 0; i < buffer.Length; i++) buffer[i] = (byte)DataFormat.EMPTY;
        if (Input.touchCount > 0)
        {
            int i;
            byte[] msg = Encoding.UTF8.GetBytes("save");
            buffer[0] = (byte)DataFormat.TEXT;
            for (i = 0; i < Math.Min(buffer.Length-2, msg.Length); i++)
                buffer[i+1] = msg[i];
            buffer[i+1] = ETX;
        }
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            Application.Quit();
        }
        
        data_sock.Send(buffer, 1024, SocketFlags.None); // Client must send first.
        data_sock.Receive(buffer, 1024, SocketFlags.None);
        // do something with `buffer`.
    }

    void OnApplicationQuit()
    {
        if (image_sock != null) image_sock.Close();
        if (data_sock != null)
        {
            int i;
            byte[] msg = Encoding.UTF8.GetBytes("exit");
            buffer[0] = (byte)DataFormat.TEXT;
            for (i = 0; i < Math.Min(buffer.Length - 2, msg.Length); i++)
                buffer[i + 1] = msg[i];
            buffer[i + 1] = ETX;

            data_sock.Send(buffer, 1024, SocketFlags.None);
            data_sock.Close();
        }
    }

    IEnumerator TakePhoto()
    {
        while (true) {
            yield return new WaitForSeconds(.1f);
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

                SetText("DebugText", bytes.Length.ToString());

                image_sock.Send(bytes, SocketFlags.None);
            }
            catch (Exception e)
            {
                SetText("DebugText", e.ToString());
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